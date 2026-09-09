#!/usr/bin/env python3
"""PSYCH 302/305 Canvas helpers. Reuses the Psych275 Canvas client and token."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
STUDENT_TEMPLATE = ROOT / "student_template"
OUT = ROOT / "out"
IDS_PATH = OUT / "ids.json"
PSYCH275_PIPELINE = Path("/Users/kylemathewson/Teaching/Psych275_Instructor/pipeline")
GITHUB_OWNER = "kylemath"
GITHUB_USER_RE = re.compile(r"^[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}$")
FORBIDDEN_TEMPLATE_NAMES = {".env", "pipeline"}

FORM_KEYS = (
    "GitHub username",
    "GitHub profile",
    "Account",
    "Education application",
    "Repo consent",
    "No paid Copilot",
)


def _load_env() -> None:
    sys.path.insert(0, str(PSYCH275_PIPELINE))
    from dotenv import load_dotenv

    load_dotenv(PSYCH275_PIPELINE / ".env")
    load_dotenv(ROOT / ".env", override=True)
    os.environ.setdefault("CANVAS_COURSE_ID", "35483")


def _client():
    _load_env()
    from lib.canvas import CanvasClient

    return CanvasClient()


def _notify_request(client, method: str, path: str, **kwargs):
    """Student-visible writes: allow Canvas email, unlike the 275 plant path."""
    resp = client.session.request(method, client._url(path), timeout=60, **kwargs)
    if resp.status_code >= 400:
        from lib.canvas import CanvasError

        raise CanvasError(f"{method} {path} → {resp.status_code}: {resp.text[:800]}")
    return resp.json() if resp.content else None


def _read(name: str) -> str:
    return (TEMPLATES / name).read_text(encoding="utf-8")


def _save_ids(update: dict) -> dict:
    OUT.mkdir(exist_ok=True)
    data = {}
    if IDS_PATH.exists():
        data = json.loads(IDS_PATH.read_text())
    data.update(update)
    IDS_PATH.write_text(json.dumps(data, indent=2) + "\n")
    return data


def cmd_courses(_: argparse.Namespace) -> None:
    client = _client()
    for row in client.list_courses():
        print(f"{row.get('id')}\t{row.get('course_code')}\t{row.get('name')}")


def cmd_week0_create(args: argparse.Namespace) -> None:
    client = _client()
    cid = client.require_course()
    name = "Week 0 · GitHub username"
    existing = client.find_assignment_by_name(name)
    if existing and not args.replace:
        print(f"exists {existing['id']} {existing.get('html_url')}")
        _save_ids({"week0_assignment_id": existing["id"], "course_id": int(cid)})
        return

    assignment = _notify_request(
        client,
        "POST",
        f"/courses/{cid}/assignments",
        json={
            "assignment": {
                "name": name,
                "description": _read("week0_assignment.html"),
                "submission_types": ["online_text_entry"],
                "points_possible": 1,
                "grading_type": "pass_fail",
                "published": True,
                "allowed_attempts": -1,
                "due_at": "2026-09-02T21:00:00-06:00",
                "omit_from_final_grade": True,
                "notify_of_update": True,
            }
        },
    )
    announcement = _notify_request(
        client,
        "POST",
        f"/courses/{cid}/discussion_topics",
        json={
            "title": "Week 0 is up: GitHub username before Wednesday 18:00",
            "message": _read("week0_announcement.html"),
            "is_announcement": True,
            "published": True,
        },
    )
    ids = _save_ids(
        {
            "course_id": int(cid),
            "week0_assignment_id": assignment["id"],
            "week0_announcement_id": announcement.get("id"),
            "week0_assignment_url": assignment.get("html_url"),
        }
    )
    print(json.dumps(ids, indent=2))


def parse_week0_body(body: str) -> dict:
    text = re.sub(r"<[^>]+>", "\n", body or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    found = {}
    for key in FORM_KEYS:
        m = re.search(rf"{re.escape(key)}\s*:\s*(\S[^\n]*)", text, re.I)
        found[key] = (m.group(1).strip() if m else "")
    username = re.sub(r"^@", "", found.get("GitHub username", "")).strip()
    profile = found.get("GitHub profile", "").strip()
    if username and not profile:
        profile = f"https://github.com/{username}"
    if not username and profile:
        m = re.search(r"github\.com/([A-Za-z0-9-]+)", profile)
        if m:
            username = m.group(1)
    return {
        "github_username": username,
        "github_profile": profile,
        "account": found.get("Account", "").lower(),
        "education": found.get("Education application", "").lower(),
        "repo_consent": found.get("Repo consent", "").lower(),
        "no_paid_copilot": found.get("No paid Copilot", "").lower(),
        "raw_keys": found,
    }


def cmd_week0_pull(_: argparse.Namespace) -> None:
    client = _client()
    ids = json.loads(IDS_PATH.read_text()) if IDS_PATH.exists() else {}
    aid = os.environ.get("CANVAS_WEEK0_ASSIGNMENT_ID") or ids.get("week0_assignment_id")
    if not aid:
        raise SystemExit("No Week 0 assignment id. Run week0-create first.")
    rows = []
    for sub in client.list_submissions(aid):
        user = sub.get("user") or {}
        parsed = parse_week0_body(sub.get("body") or "")
        rows.append(
            {
                "canvasUserId": sub.get("user_id"),
                "canvasName": user.get("name"),
                "sortableName": user.get("sortable_name"),
                "sisUserId": user.get("sis_user_id"),
                "workflow": sub.get("workflow_state"),
                **parsed,
            }
        )
    OUT.mkdir(exist_ok=True)
    dest = OUT / "week0_roster.json"
    dest.write_text(json.dumps(rows, indent=2) + "\n")
    submitted = [r for r in rows if r["github_username"]]
    print(f"wrote {dest}  {len(submitted)}/{len(rows)} with a username")


URL_RE = re.compile(r"https?://[^\s<>\"']+")


def _plain_text(body: str) -> str:
    text = re.sub(r"<[^>]+>", "\n", body or "")
    text = text.replace("&nbsp;", " ").replace("&amp;", "&")
    return re.sub(r"\n+", "\n", text).strip()


def parse_week1_body(body: str) -> dict:
    """Pull the four GitHub links plus leftover text from a Week 1 Canvas box."""
    raw = body or ""
    text = _plain_text(raw)
    urls = []
    seen = set()
    for match in URL_RE.findall(raw) + URL_RE.findall(text):
        url = match.rstrip(").,;\"'")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    pages, prs, forks, repos, other = [], [], [], [], []
    for url in urls:
        low = url.lower()
        if ".github.io" in low:
            pages.append(url)
        elif "/pull/" in low:
            prs.append(url)
        elif "psych302-305-kylemathewson" in low:
            forks.append(url)
        elif "github.com" in low:
            repos.append(url)
        else:
            other.append(url)
    return {
        "urls": urls,
        "own_repo_urls": repos,
        "pages_urls": pages,
        "fork_urls": forks,
        "pr_urls": prs,
        "other_urls": other,
        "text": text[:4000],
        "has_disclosure": bool(re.search(r"copilot|no copilot|ai disclosure|used tonight", text, re.I)),
    }


def cmd_week1_pull(_: argparse.Namespace) -> None:
    """Harvest Week 1 Canvas boxes. Writes out/week1_roster.json. Does not grade."""
    client = _client()
    ids = json.loads(IDS_PATH.read_text()) if IDS_PATH.exists() else {}
    weekly = ids.get("weekly_assignments") or {}
    aid = (weekly.get("week01") or {}).get("id")
    if not aid:
        raise SystemExit("No Week 1 assignment id in out/ids.json. Run modules-create first.")
    rows = []
    for sub in client.list_submissions(aid):
        user = sub.get("user") or {}
        parsed = parse_week1_body(sub.get("body") or "")
        rows.append(
            {
                "canvasUserId": sub.get("user_id"),
                "canvasName": user.get("name"),
                "sortableName": user.get("sortable_name"),
                "sisUserId": user.get("sis_user_id"),
                "workflow": sub.get("workflow_state"),
                "submitted_at": sub.get("submitted_at"),
                "grade": sub.get("grade"),
                "score": sub.get("score"),
                **parsed,
            }
        )
    OUT.mkdir(exist_ok=True)
    dest = OUT / "week1_roster.json"
    dest.write_text(json.dumps(rows, indent=2) + "\n")
    submitted = [r for r in rows if r.get("submitted_at")]
    with_pages = [r for r in submitted if r.get("pages_urls")]
    with_pr = [r for r in submitted if r.get("pr_urls")]
    print(f"wrote {dest}  {len(submitted)} submitted / {len(rows)} rows  pages={len(with_pages)} prs={len(with_pr)}")


def cmd_week0_grade(args: argparse.Namespace) -> None:
    """POST complete/incomplete only. Username present and non-empty → complete."""
    roster_path = OUT / "week0_roster.json"
    if not roster_path.exists():
        raise SystemExit("No week0_roster.json. Run week0-pull first.")
    rows = json.loads(roster_path.read_text())
    ids = json.loads(IDS_PATH.read_text()) if IDS_PATH.exists() else {}
    aid = os.environ.get("CANVAS_WEEK0_ASSIGNMENT_ID") or ids.get("week0_assignment_id")
    if not aid:
        raise SystemExit("No Week 0 assignment id. Run week0-create first.")
    client = _client()
    cid = client.require_course()
    n_complete = 0
    n_incomplete = 0
    for row in rows:
        uid = row.get("canvasUserId")
        if uid is None:
            print(f"skip  no canvasUserId  {row.get('canvasName')}")
            continue
        username = (row.get("github_username") or "").strip()
        grade = "complete" if username else "incomplete"
        if args.dry_run:
            print(f"dry   {uid}\t{grade}\t{row.get('canvasName')}")
        else:
            _notify_request(
                client,
                "PUT",
                f"/courses/{cid}/assignments/{aid}/submissions/{uid}",
                data={"submission[posted_grade]": grade},
            )
            print(f"put   {uid}\t{grade}\t{row.get('canvasName')}")
        if grade == "complete":
            n_complete += 1
        else:
            n_incomplete += 1
    mode = "dry-run" if args.dry_run else "posted"
    print(f"{mode}  {n_complete} complete / {n_incomplete} incomplete / {len(rows)} rows")


def _valid_github_username(name: str) -> bool:
    return bool(GITHUB_USER_RE.fullmatch(name or ""))


def _consent_yes(value: str) -> bool:
    return (value or "").strip().lower() == "yes"


def _assert_safe_template(src: Path) -> None:
    if not src.is_dir():
        raise SystemExit(f"Missing student template: {src}")
    for path in src.rglob("*"):
        rel = path.relative_to(src)
        parts = set(rel.parts)
        if parts & FORBIDDEN_TEMPLATE_NAMES:
            raise SystemExit(f"Refusing template path that looks like instructor secrets: {rel}")
        if path.is_file() and path.name == ".env":
            raise SystemExit(f"Refusing to mint a .env: {rel}")


def _gh(*args: str, check: bool = True) -> subprocess.CompletedProcess:
    env = os.environ.copy()
    env["GH_PROMPT_DISABLED"] = "1"
    return subprocess.run(["gh", *args], capture_output=True, text=True, check=check, env=env)


def _repo_exists(full_name: str) -> bool:
    result = _gh("repo", "view", full_name, "--json", "name,url,isPrivate", check=False)
    return result.returncode == 0


def _repo_full_name(username: str) -> str:
    return f"{GITHUB_OWNER}/psych302-305-{username}"


def build_mint_plan(rows: list[dict]) -> list[dict]:
    """Classify each roster row. Network: existence check only for eligible usernames."""
    plan = []
    for row in rows:
        username = (row.get("github_username") or "").strip()
        consent = (row.get("repo_consent") or "").strip()
        item = {
            "canvasUserId": row.get("canvasUserId"),
            "canvasName": row.get("canvasName"),
            "github_username": username,
            "repo_consent": consent,
            "repo": None,
            "action": None,
            "reason": None,
        }
        if not username:
            item["action"] = "skip-no-username"
            item["reason"] = "no parsed GitHub username"
        elif not _consent_yes(consent):
            item["action"] = "skip-no-consent"
            item["reason"] = f"repo_consent={consent or '(empty)'}"
        elif not _valid_github_username(username):
            item["action"] = "skip-invalid-username"
            item["reason"] = f"username not a legal GitHub login: {username!r}"
        else:
            full = _repo_full_name(username)
            item["repo"] = full
            if _repo_exists(full):
                item["action"] = "skip-exists"
                item["reason"] = "same-name repo already exists; will not overwrite or force-push"
            else:
                item["action"] = "create"
                item["reason"] = "parsed username and repo_consent=yes"
        plan.append(item)
    return plan


def _copy_student_workspace(dest: Path) -> None:
    _assert_safe_template(STUDENT_TEMPLATE)
    shutil.copytree(
        STUDENT_TEMPLATE,
        dest,
        ignore=shutil.ignore_patterns(".env", "pipeline", ".git"),
    )
    _assert_safe_template(dest)


def _template_files() -> list[Path]:
    _assert_safe_template(STUDENT_TEMPLATE)
    files: list[Path] = []
    for path in STUDENT_TEMPLATE.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(STUDENT_TEMPLATE)
        parts = set(rel.parts)
        if parts & FORBIDDEN_TEMPLATE_NAMES or path.name == ".env":
            continue
        files.append(rel)
    return files


def _repo_file_paths(full: str) -> set[str]:
    result = _gh("api", f"repos/{full}/git/trees/HEAD?recursive=1", check=False)
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout or f"could not list {full}")
    payload = json.loads(result.stdout)
    paths = set()
    for node in payload.get("tree") or []:
        if node.get("type") == "blob" and node.get("path"):
            paths.add(node["path"])
    return paths


def _git_local_identity(dest: Path) -> None:
    subprocess.run(["git", "config", "user.name", "kylemath"], cwd=dest, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "kylemath@users.noreply.github.com"],
        cwd=dest,
        check=True,
        capture_output=True,
    )


def build_sync_plan(rows: list[dict]) -> list[dict]:
    """For existing minted repos, list template files that are still missing."""
    mint_plan = build_mint_plan(rows)
    template_files = _template_files()
    plan = []
    for item in mint_plan:
        row = {
            "canvasUserId": item["canvasUserId"],
            "canvasName": item["canvasName"],
            "github_username": item["github_username"],
            "repo": item["repo"],
            "action": None,
            "missing": [],
            "reason": item["reason"],
        }
        if item["action"] != "skip-exists":
            row["action"] = item["action"]
            plan.append(row)
            continue
        try:
            existing = _repo_file_paths(item["repo"])
        except RuntimeError as exc:
            row["action"] = "error-list"
            row["reason"] = str(exc)[:200]
            plan.append(row)
            continue
        missing = [rel.as_posix() for rel in template_files if rel.as_posix() not in existing]
        row["missing"] = missing
        if missing:
            row["action"] = "add-missing"
            row["reason"] = f"{len(missing)} template file(s) absent; will add only those"
        else:
            row["action"] = "skip-complete"
            row["reason"] = "all current template files already present"
        plan.append(row)
    return plan


def _sync_missing_files(username: str, missing: list[str]) -> dict:
    """Clone, copy only missing template files, commit, regular push. Never force."""
    full = _repo_full_name(username)
    if not missing:
        return {"action": "skip-complete", "repo": full, "added": []}
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / f"psych302-305-{username}"
        result = _gh("repo", "clone", full, str(dest), "--", "--depth", "1", check=False)
        if result.returncode != 0:
            raise RuntimeError(result.stderr or result.stdout)
        added = []
        for rel in missing:
            src = STUDENT_TEMPLATE / rel
            out = dest / rel
            if not src.is_file():
                continue
            if out.exists():
                continue
            out.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, out)
            added.append(rel)
        if not added:
            return {"action": "skip-complete", "repo": full, "added": []}
        _git_local_identity(dest)
        subprocess.run(["git", "add", "--", *added], cwd=dest, check=True, capture_output=True)
        staged = subprocess.run(["git", "diff", "--cached", "--name-only"], cwd=dest, check=True, capture_output=True, text=True)
        if not staged.stdout.strip():
            return {"action": "skip-complete", "repo": full, "added": []}
        subprocess.run(
            [
                "git",
                "commit",
                "-m",
                "Add Week 4 report pipeline files (missing template only; no overwrite)",
            ],
            cwd=dest,
            check=True,
            capture_output=True,
        )
        push = subprocess.run(["git", "push", "origin", "HEAD"], cwd=dest, check=False, capture_output=True, text=True)
        if push.returncode != 0:
            raise RuntimeError(push.stderr or push.stdout)
    return {"action": "added", "repo": full, "added": added}


def _mint_new_repo(username: str) -> dict:
    full = _repo_full_name(username)
    if _repo_exists(full):
        return {"ok": False, "action": "skip-exists", "repo": full, "html_url": None}
    with tempfile.TemporaryDirectory() as tmp:
        dest = Path(tmp) / f"psych302-305-{username}"
        _copy_student_workspace(dest)
        subprocess.run(["git", "init", "-b", "main"], cwd=dest, check=True, capture_output=True)
        subprocess.run(["git", "config", "user.name", "kylemath"], cwd=dest, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.email", "kylemath@users.noreply.github.com"],
            cwd=dest,
            check=True,
            capture_output=True,
        )
        subprocess.run(["git", "add", "-A"], cwd=dest, check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial PSYCH 302/305 studio workspace"],
            cwd=dest,
            check=True,
            capture_output=True,
        )
        _gh(
            "repo",
            "create",
            full,
            "--private",
            "--source",
            str(dest),
            "--remote",
            "origin",
            "--push",
        )
    view = _gh("repo", "view", full, "--json", "url,isPrivate")
    meta = json.loads(view.stdout)
    return {
        "ok": True,
        "action": "create",
        "repo": full,
        "html_url": meta.get("url"),
        "isPrivate": meta.get("isPrivate"),
    }


def _ensure_collaborator(username: str) -> None:
    full = _repo_full_name(username)
    result = _gh(
        "api",
        "-X",
        "PUT",
        f"repos/{full}/collaborators/{username}",
        "-f",
        "permission=push",
        check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(result.stderr or result.stdout)


def cmd_repos_mint(args: argparse.Namespace) -> None:
    """Mint thin private studio repos. Default is dry-run; pass --apply to create."""
    roster_path = OUT / "week0_roster.json"
    if not roster_path.exists():
        raise SystemExit("No week0_roster.json. Run week0-pull first.")
    _assert_safe_template(STUDENT_TEMPLATE)
    rows = json.loads(roster_path.read_text())
    plan = build_mint_plan(rows)
    counts: dict[str, int] = {}
    for item in plan:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
        repo = item["repo"] or "—"
        print(f"{item['action']:<24} {item['canvasUserId']}\t{item['canvasName']}\t{item['github_username'] or '—'}\t{repo}\t{item['reason']}")
    print("plan  " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    apply = bool(args.apply) and not args.dry_run
    if not apply:
        print("dry-run only. Pass --apply to create repos for action=create.")
        return

    for item in plan:
        try:
            if item["action"] == "create":
                result = _mint_new_repo(item["github_username"])
                if result["action"] == "skip-exists":
                    print(f"race-skip-exists         {item['canvasName']}\t{result['repo']}")
                    _ensure_collaborator(item["github_username"])
                    print(f"collaborator             {item['github_username']} push on {result['repo']}")
                    continue
                _ensure_collaborator(item["github_username"])
                print(
                    f"created                  {result['repo']}\t{result.get('html_url')}\tcollab={item['github_username']}"
                )
            elif item["action"] == "skip-exists":
                _ensure_collaborator(item["github_username"])
                print(
                    f"collaborator             {item['github_username']} push on {item['repo']} (existing, not overwritten)"
                )
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            err = getattr(exc, "stderr", None) or str(exc)
            print(f"error                    {item['canvasName']}\t{item.get('repo') or item['github_username']}\t{err[:400]}")


def cmd_repos_sync(args: argparse.Namespace) -> None:
    """Add missing student_template files to existing repos. Never overwrite or force-push."""
    roster_path = OUT / "week0_roster.json"
    if not roster_path.exists():
        raise SystemExit("No week0_roster.json. Run week0-pull first.")
    _assert_safe_template(STUDENT_TEMPLATE)
    rows = json.loads(roster_path.read_text())
    plan = build_sync_plan(rows)
    counts: dict[str, int] = {}
    for item in plan:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
        extra = f"\t{', '.join(item['missing'])}" if item["missing"] else ""
        print(
            f"{item['action']:<24} {item['canvasUserId']}\t{item['canvasName']}\t"
            f"{item['github_username'] or '—'}\t{item['repo'] or '—'}\t{item['reason']}{extra}"
        )
    print("plan  " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))

    apply = bool(args.apply) and not args.dry_run
    if not apply:
        print("dry-run only. Pass --apply to add missing files on action=add-missing.")
        return

    for item in plan:
        if item["action"] != "add-missing":
            continue
        try:
            result = _sync_missing_files(item["github_username"], item["missing"])
            print(
                f"{result['action']:<24} {item['canvasName']}\t{result['repo']}\t"
                f"added={','.join(result.get('added') or []) or '—'}"
            )
        except (RuntimeError, subprocess.CalledProcessError) as exc:
            err = getattr(exc, "stderr", None) or str(exc)
            print(f"error                    {item['canvasName']}\t{item['repo']}\t{err[:400]}")


def cmd_modules_create(_: argparse.Namespace) -> None:
    from course_modules import run

    client = _client()
    run(client, lambda method, path, **kw: _notify_request(client, method, path, **kw), _read, _save_ids)


def main() -> None:
    p = argparse.ArgumentParser(description="PSYCH 302/305 Canvas studio pipeline")
    sub = p.add_subparsers(dest="cmd", required=True)
    sub.add_parser("courses").set_defaults(func=cmd_courses)
    c = sub.add_parser("week0-create")
    c.add_argument("--replace", action="store_true")
    c.set_defaults(func=cmd_week0_create)
    sub.add_parser("week0-pull").set_defaults(func=cmd_week0_pull)
    sub.add_parser("week1-pull").set_defaults(func=cmd_week1_pull)
    g = sub.add_parser("week0-grade")
    g.add_argument("--dry-run", action="store_true", help="Print complete/incomplete; do not PUT")
    g.set_defaults(func=cmd_week0_grade)
    m = sub.add_parser("repos-mint")
    m.add_argument("--dry-run", action="store_true", help="Print the plan only (default if --apply is omitted)")
    m.add_argument("--apply", action="store_true", help="Create private repos and add collaborators")
    m.set_defaults(func=cmd_repos_mint)
    s = sub.add_parser("repos-sync")
    s.add_argument("--dry-run", action="store_true", help="Print the plan only (default if --apply is omitted)")
    s.add_argument("--apply", action="store_true", help="Add missing template files; never overwrite or force-push")
    s.set_defaults(func=cmd_repos_sync)
    sub.add_parser("modules-create").set_defaults(func=cmd_modules_create)
    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
