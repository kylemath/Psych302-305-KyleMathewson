"""Roster, weekly harvest/grade, and dropped-student repo cleanup for PSYCH 302/305."""

from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from urllib.parse import urlparse

KEEP_USERNAMES = {"kylemath"}
HANDBOOK_REPO = "kylemath/Psych302-305-KyleMathewson"
CURRENT_STATES = {"active", "invited", "creation_pending"}
FORMER_STATES = {"inactive", "completed", "rejected", "deleted"}
TEST_NAME_RE = re.compile(r"test student", re.I)
DISCLOSURE_RE = re.compile(
    r"copilot|no copilot|chat\s*gpt|openai|cursor|claude|gemini|used tonight|ai disclosure|\bai\b",
    re.I,
)
WEEK2_NOTE_PATHS = (
    "week02-rt/README.md",
    "lab-notes/week02.md",
    "week02.md",
)
WEEK2_PAGE_PATHS = (
    "week02-rt/rt.html",
    "rt/rt.html",
    "rt.html",
)
DEFAULT_SKETCH_MARKERS = (
    'let nTrials = 20;',
    'let markColor = [232, 184, 109];',
    'when the square appears.',
)
LIMITATION_RE = re.compile(
    r"limit|practice|anticipat|fatigue|small n|self-report|\blie\b|tired|distract|trackpad|mouse|sample size|refresh|monitor|got used",
    re.I,
)
STRONG_PERSONAL_RE = re.compile(
    r"circle|ellipse|star|bottle|distractor|random (loc|pos|place)|confetti|space invader|beer|turquoise|sniper|burst|go/no.go",
    re.I,
)
BLOB_RE = re.compile(r"github\.com/([^/]+)/([^/]+)/blob/([^/]+)/(.+)", re.I)
CLASS_DEMO_RE = re.compile(
    r"kylemath\.github\.io/psych302-305-kylemathewson|github\.com/kylemath/psych302-305-kylemathewson/",
    re.I,
)


def _skip_row(row: dict) -> bool:
    name = row.get("canvasName") or ""
    return bool(TEST_NAME_RE.search(name))


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paginate_enrollments(client, states: list[str]) -> list[dict]:
    cid = client.require_course()
    out: list[dict] = []
    page = 1
    while True:
        batch = client._request(
            "GET",
            f"/courses/{cid}/enrollments",
            params={
                "type[]": ["StudentEnrollment"],
                "state[]": states,
                "per_page": 100,
                "page": page,
            },
        )
        if not batch:
            break
        out.extend(batch)
        if len(batch) < 100:
            break
        page += 1
    return out


def _enrollment_row(enr: dict) -> dict:
    user = enr.get("user") or {}
    return {
        "canvasUserId": enr.get("user_id") or user.get("id"),
        "canvasName": user.get("name"),
        "sortableName": user.get("sortable_name"),
        "sisUserId": user.get("sis_user_id"),
        "enrollment_state": enr.get("enrollment_state"),
        "enrollment_id": enr.get("id"),
        "last_activity_at": enr.get("last_activity_at"),
    }


def load_roster() -> dict:
    from studio_pipeline import OUT

    path = OUT / "roster.json"
    if not path.exists():
        raise SystemExit("No roster.json. Run roster-pull first.")
    return json.loads(path.read_text())


def current_user_ids(roster: dict | None = None) -> set[int]:
    data = roster or load_roster()
    ids = set()
    for row in data.get("current") or []:
        uid = row.get("canvasUserId")
        if uid is not None and not _skip_row(row):
            ids.add(int(uid))
    return ids


def cmd_roster_pull(_: object) -> None:
    """Current vs former Canvas student enrollments. Writes out/roster.json."""
    from studio_pipeline import OUT, _client

    client = _client()
    current_raw = _paginate_enrollments(client, sorted(CURRENT_STATES))
    former_raw = _paginate_enrollments(client, sorted(FORMER_STATES))
    current_by_id: dict[int, dict] = {}
    for enr in current_raw:
        row = _enrollment_row(enr)
        uid = row.get("canvasUserId")
        if uid is None or _skip_row(row):
            continue
        current_by_id[int(uid)] = row
    former = []
    seen_former = set()
    for enr in former_raw:
        row = _enrollment_row(enr)
        uid = row.get("canvasUserId")
        if uid is None or _skip_row(row):
            continue
        uid = int(uid)
        if uid in current_by_id or uid in seen_former:
            continue
        seen_former.add(uid)
        former.append(row)
    current = sorted(current_by_id.values(), key=lambda r: (r.get("sortableName") or "", r.get("canvasName") or ""))
    former.sort(key=lambda r: (r.get("sortableName") or "", r.get("canvasName") or ""))
    payload = {
        "pulled_at": _now(),
        "course_id": int(client.require_course()),
        "current": current,
        "former": former,
    }
    OUT.mkdir(exist_ok=True)
    dest = OUT / "roster.json"
    dest.write_text(json.dumps(payload, indent=2) + "\n")
    print(f"wrote {dest}  current={len(current)}  former={len(former)}")
    if former:
        print("no longer enrolled:")
        for row in former:
            print(f"  {row.get('enrollment_state'):<12} {row.get('canvasUserId')}\t{row.get('canvasName')}")


def parse_week2_body(body: str) -> dict:
    from studio_pipeline import URL_RE, _plain_text

    raw = body or ""
    text = _plain_text(raw)
    urls = []
    seen = set()
    for match in URL_RE.findall(raw) + URL_RE.findall(text):
        url = match.rstrip(").,;\"'")
        if url not in seen:
            seen.add(url)
            urls.append(url)
    paths = re.findall(r"(?:[\w.-]+/)*[\w.-]+\.(?:md|html|htm|csv|txt)", text, re.I)
    pred = re.search(
        r"predict(?:ed)?(?:\s+mean)?(?:\s*RT)?(?:\s+the following data)?\s*[:\-=]?\s*(?:n\s*[=:]\s*\d+\s*)?(?:mean\s*[=:]?\s*)?(\d+(?:\.\d+)?)",
        text,
        re.I,
    )
    if not pred:
        pred = re.search(r"predict(?:ed)?(?:.{0,80}?)(\d+(?:\.\d+)?)\s*m", text, re.I)
    n = re.search(r"\bn\s*[=:]\s*(\d+)", text, re.I)
    mean = re.search(r"mean(?:\s*RT)?\s*[=:]\s*(\d+(?:\.\d+)?)", text, re.I)
    sd = re.search(
        r"(?:(?<![a-z])sd|s\.d\.|stdev|standard deviation|sample sd)\s*[=:\-]?\s*(\d+(?:\.\d+)?)",
        text,
        re.I,
    )
    limitation = bool(LIMITATION_RE.search(text))
    personalized = bool(
        re.search(
            r"personaliz|modif|changed|circle|colour|color|sound|shape|delay|trial count|nTrials|nWanted|I (made|edited|rewrote)",
            text,
            re.I,
        )
        or STRONG_PERSONAL_RE.search(text)
    )
    return {
        "urls": urls,
        "paths": paths,
        "text": text[:4000],
        "predicted_mean": pred.group(1) if pred else "",
        "n": n.group(1) if n else "",
        "mean_rt": mean.group(1) if mean else "",
        "sd": sd.group(1) if sd else "",
        "has_limitation": limitation,
        "names_personalization": personalized,
        "has_disclosure": bool(DISCLOSURE_RE.search(text)),
    }


def _username_for(row: dict, week0_by_id: dict[int, dict]) -> str:
    from studio_pipeline import _valid_github_username

    uid = row.get("canvasUserId")
    linked = week0_by_id.get(int(uid)) if uid is not None else {}
    candidates = []
    for value in (
        row.get("github_username"),
        (linked or {}).get("github_username"),
        (linked or {}).get("github_profile"),
        row.get("github_profile"),
    ):
        if not value:
            continue
        m = re.search(r"github\.com/([A-Za-z0-9-]+)", str(value), re.I)
        candidates.append(m.group(1) if m else str(value).strip().lstrip("@"))
    for cand in candidates:
        if _valid_github_username(cand):
            return cand
    return ""


def _load_week0_by_id() -> dict[int, dict]:
    from studio_pipeline import OUT

    path = OUT / "week0_roster.json"
    if not path.exists():
        return {}
    out = {}
    for row in json.loads(path.read_text()):
        uid = row.get("canvasUserId")
        if uid is not None:
            out[int(uid)] = row
    return out


def _repo_raw(full: str, path: str) -> str | None:
    from studio_pipeline import _gh

    result = _gh(
        "api",
        f"repos/{full}/contents/{path}",
        "-H",
        "Accept: application/vnd.github.raw",
        check=False,
    )
    if result.returncode != 0:
        return None
    return result.stdout


def _inspect_week2_repo(username: str) -> dict:
    from studio_pipeline import _repo_exists, _repo_file_paths, _repo_full_name

    if not username:
        return {"repo": None, "exists": False, "files": [], "note_path": "", "page_path": "", "csv_paths": [], "page_looks_default": None}
    full = _repo_full_name(username)
    if not _repo_exists(full):
        return {"repo": full, "exists": False, "files": [], "note_path": "", "page_path": "", "csv_paths": [], "page_looks_default": None}
    try:
        files = sorted(_repo_file_paths(full))
    except RuntimeError as exc:
        return {
            "repo": full,
            "exists": True,
            "files": [],
            "note_path": "",
            "page_path": "",
            "csv_paths": [],
            "page_looks_default": None,
            "error": str(exc)[:200],
        }
    note = next((p for p in WEEK2_NOTE_PATHS if p in files), "")
    page = next((p for p in WEEK2_PAGE_PATHS if p in files), "")
    csvs = [
        p
        for p in files
        if p.lower().endswith(".csv")
        and not p.startswith("week03-")
        and not p.startswith("week10-")
        and "inventory" not in p.lower()
    ]
    defaultish = None
    pages_present = [p for p in WEEK2_PAGE_PATHS if p in files]
    for candidate in pages_present or ([page] if page else []):
        html = _repo_raw(full, candidate) or ""
        if not html:
            continue
        hits = sum(1 for marker in DEFAULT_SKETCH_MARKERS if marker in html)
        looks_default = hits >= 3
        if STRONG_PERSONAL_RE.search(html) or "ellipse(" in html or "triangle(" in html or "star" in html.lower():
            looks_default = False
        if defaultish is None or (defaultish is True and looks_default is False):
            defaultish = looks_default
            page = candidate
    return {
        "repo": full,
        "exists": True,
        "files": files,
        "note_path": note,
        "page_path": page,
        "csv_paths": csvs,
        "page_looks_default": defaultish,
        "old_layout": any(p.startswith("lab-notes/") or p.startswith("rt/") or p.startswith("data/") for p in files),
        "new_layout": any(p.startswith("week02-rt/") for p in files),
    }


def _inspect_pasted_urls(urls: list[str]) -> dict:
    from studio_pipeline import _gh

    notes, pages, csvs = [], [], []
    for url in urls:
        if CLASS_DEMO_RE.search(url or ""):
            continue
        m = BLOB_RE.search(url or "")
        if not m:
            continue
        owner, repo, ref, path = m.group(1), m.group(2), m.group(3), m.group(4).split("?")[0]
        result = _gh("api", f"repos/{owner}/{repo}/contents/{path}?ref={ref}", check=False)
        if result.returncode != 0:
            continue
        low = path.lower()
        rec = {"url": url, "path": path, "repo": f"{owner}/{repo}"}
        if low.endswith((".md", ".txt")):
            notes.append(rec)
        elif low.endswith((".html", ".htm")):
            pages.append(rec)
        elif low.endswith(".csv"):
            csvs.append(rec)
    return {"notes": notes, "pages": pages, "csvs": csvs}


def cmd_week2_pull(_: object) -> None:
    """Harvest Week 2 Canvas boxes and inspect private repos. Does not grade."""
    from studio_pipeline import OUT, _client, _plain_text, _weekly_assignment_id

    client = _client()
    aid = _weekly_assignment_id(client, 2)
    week0 = _load_week0_by_id()
    rows = []
    for sub in client.list_submissions(aid):
        user = sub.get("user") or {}
        parsed = parse_week2_body(sub.get("body") or "")
        row = {
            "canvasUserId": sub.get("user_id"),
            "canvasName": user.get("name"),
            "sortableName": user.get("sortable_name"),
            "sisUserId": user.get("sis_user_id"),
            "workflow": sub.get("workflow_state"),
            "submitted_at": sub.get("submitted_at"),
            "grade": sub.get("grade"),
            "score": sub.get("score"),
            "github_username": _username_for({"canvasUserId": sub.get("user_id")}, week0),
            **parsed,
        }
        if _skip_row(row):
            continue
        row["repo_inspect"] = _inspect_week2_repo(row["github_username"])
        row["pasted_files"] = _inspect_pasted_urls(row.get("urls") or [])
        rows.append(row)
    OUT.mkdir(exist_ok=True)
    dest = OUT / "week2_roster.json"
    dest.write_text(json.dumps(rows, indent=2) + "\n")
    submitted = [r for r in rows if r.get("submitted_at")]
    with_note = [r for r in submitted if (r.get("repo_inspect") or {}).get("note_path")]
    with_csv = [r for r in submitted if (r.get("repo_inspect") or {}).get("csv_paths")]
    with_page = [r for r in submitted if (r.get("repo_inspect") or {}).get("page_path")]
    print(
        f"wrote {dest}  {len(submitted)} submitted / {len(rows)} rows  "
        f"notes={len(with_note)} pages={len(with_page)} csvs={len(with_csv)}"
    )


def _http_ok(url: str) -> tuple[bool | None, str]:
    import requests

    if not url:
        return False, "missing"
    try:
        resp = requests.get(
            url,
            timeout=15,
            allow_redirects=True,
            headers={"User-Agent": "psych302-instructor-grader/1.0"},
        )
        if resp.status_code == 404:
            return False, "404"
        if 200 <= resp.status_code < 400:
            return True, str(resp.status_code)
        return None, str(resp.status_code)
    except requests.RequestException as exc:
        return None, str(exc)[:120]


def _parse_github_repo(url: str) -> tuple[str, str] | None:
    if not url:
        return None
    parsed = urlparse(url)
    host = (parsed.netloc or "").lower()
    if host == "github.com":
        parts = [p for p in parsed.path.split("/") if p]
        if len(parts) >= 2:
            return parts[0], parts[1].removesuffix(".git")
    if host.endswith(".github.io"):
        user = host.split(".")[0]
        parts = [p for p in parsed.path.split("/") if p]
        repo = parts[0] if parts else f"{user}.github.io"
        return user, repo
    return None


def _gh_repo_ok(url: str) -> tuple[bool | None, str]:
    from studio_pipeline import _gh

    parsed = _parse_github_repo(url)
    if not parsed:
        return False, "not a github repo url"
    owner, name = parsed
    result = _gh("api", f"repos/{owner}/{name}", "--jq", ".full_name", check=False)
    if result.returncode == 0 and result.stdout.strip():
        return True, result.stdout.strip()
    return False, (result.stderr or result.stdout or "missing")[:120]


def _fork_ok(url: str) -> tuple[bool | None, str]:
    from studio_pipeline import _gh

    parsed = _parse_github_repo(url)
    if not parsed:
        return False, "not a github repo url"
    owner, name = parsed
    result = _gh(
        "api",
        f"repos/{owner}/{name}",
        "--jq",
        "{fork:.fork,parent:.parent.full_name,name:.full_name}",
        check=False,
    )
    if result.returncode != 0:
        return False, (result.stderr or "missing")[:120]
    try:
        meta = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None, "unparsed"
    parent = (meta.get("parent") or "") if isinstance(meta, dict) else ""
    if meta.get("fork") and parent.lower() == HANDBOOK_REPO.lower():
        return True, parent
    if name.lower() == "psych302-305-kylemathewson":
        return True, f"{owner}/{name}"
    return False, f"not a handbook fork ({meta})"


def _pr_ok(url: str, username: str) -> tuple[bool | None, str]:
    from studio_pipeline import _gh

    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", url or "", re.I)
    if not m:
        return False, "not a pull url"
    owner, repo, num = m.group(1), m.group(2), m.group(3)
    if f"{owner}/{repo}".lower() != HANDBOOK_REPO.lower():
        return False, f"PR is on {owner}/{repo}, not the class repo"
    result = _gh(
        "api",
        f"repos/{owner}/{repo}/pulls/{num}",
        "--jq",
        "{state:.state,user:.user.login,head:.head.repo.full_name}",
        check=False,
    )
    if result.returncode != 0:
        return False, (result.stderr or "missing")[:120]
    try:
        meta = json.loads(result.stdout)
    except json.JSONDecodeError:
        return None, "unparsed"
    return True, f"{meta.get('state')} by {meta.get('user')}"


_CLASS_PRS = None


def _class_pr_for(username: str) -> str:
    global _CLASS_PRS
    from studio_pipeline import _gh

    if _CLASS_PRS is None:
        result = _gh(
            "pr",
            "list",
            "--repo",
            HANDBOOK_REPO,
            "--state",
            "all",
            "--limit",
            "100",
            "--json",
            "number,author,state,url",
        )
        _CLASS_PRS = json.loads(result.stdout)
    for pr in _CLASS_PRS:
        login = ((pr.get("author") or {}).get("login") or "").lower()
        if login == username.lower():
            return f"{pr.get('state')} {pr.get('url')}"
    return ""


def _named_three_changes(text: str) -> bool:
    if not text:
        return False
    numbered = re.findall(r"(?:^|\n)\s*(?:\d+[\).]|[-*])\s+\S+", text)
    if len(numbered) >= 3:
        return True
    return bool(
        re.search(
            r"(three|3)\s+(ways|changes|things|edits|custom)",
            text,
            re.I,
        )
    ) or len(re.findall(r"(changed|replaced|added|personalized|my name|about me)", text, re.I)) >= 3


def score_week1(row: dict) -> dict:
    submitted = bool(row.get("submitted_at"))
    reasons = []
    review = []
    if not submitted:
        return {
            "score": 0,
            "parts": {"repo": 0, "pages": 0, "fork": 0, "pr": 0, "changes": 0, "disclosure": 0},
            "comment": "No Canvas submission by the Tuesday due date.",
            "needs_review": False,
            "reasons": ["unsubmitted"],
        }
    own = (row.get("own_repo_urls") or row.get("urls") or [None])[0] if (row.get("own_repo_urls") or row.get("urls")) else ""
    if row.get("own_repo_urls"):
        own = row["own_repo_urls"][0]
    pages = (row.get("pages_urls") or [None])[0] or ""
    forks = (row.get("fork_urls") or [None])[0] or ""
    prs = (row.get("pr_urls") or [None])[0] or ""
    username = (row.get("github_username") or "").strip()

    repo_ok, repo_why = _gh_repo_ok(own) if own else (False, "missing")
    if not own and username:
        repo_ok, repo_why = _gh_repo_ok(f"https://github.com/{username}")
    pages_ok, pages_why = _http_ok(pages) if pages else (False, "missing")
    if pages_ok is None:
        review.append(f"pages {pages_why}")
        pages_ok = bool(pages) and "github.io" in pages.lower()
    fork_ok, fork_why = _fork_ok(forks) if forks else (False, "missing")
    if not forks:
        # A handbook-named repo URL sometimes landed in own_repo or other
        for url in row.get("urls") or []:
            ok, why = _fork_ok(url)
            if ok:
                fork_ok, fork_why = ok, why
                break
    pr_ok, pr_why = _pr_ok(prs, username) if prs else (False, "missing")
    if not pr_ok and username:
        found = _class_pr_for(username)
        if found:
            pr_ok, pr_why = True, found
    changes = _named_three_changes(row.get("text") or "")
    disclosure = bool(row.get("has_disclosure")) or bool(DISCLOSURE_RE.search(row.get("text") or ""))

    parts = {
        "repo": 2 if repo_ok else 0,
        "pages": 2 if pages_ok else 0,
        "fork": 2 if fork_ok else 0,
        "pr": 2 if pr_ok else 0,
        "changes": 1 if changes else 0,
        "disclosure": 1 if disclosure else 0,
    }
    reasons.extend(
        [
            f"repo={repo_ok} {own or '—'} {repo_why}",
            f"pages={pages_ok} {pages or '—'} {pages_why}",
            f"fork={fork_ok} {forks or '—'} {fork_why}",
            f"pr={pr_ok} {prs or '—'} {pr_why}",
            f"changes={changes}",
            f"disclosure={disclosure}",
        ]
    )
    score = sum(parts.values())
    comment = (
        f"Week 1: own repo {parts['repo']}, Pages {parts['pages']}, "
        f"fork {parts['fork']}, PR {parts['pr']}, three changes {parts['changes']}, "
        f"disclosure {parts['disclosure']}. Total {score}/10."
    )
    return {
        "score": score,
        "parts": parts,
        "comment": comment,
        "needs_review": bool(review),
        "reasons": reasons + ([f"review: {'; '.join(review)}"] if review else []),
    }


def _note_is_filled(username: str, note_path: str, canvas_text: str) -> bool:
    if not note_path:
        return bool(canvas_text and len(canvas_text) > 80)
    full = None
    from studio_pipeline import _repo_full_name

    body = _repo_raw(_repo_full_name(username), note_path) if username else ""
    if not body:
        return bool(canvas_text and len(canvas_text) > 80)
    stripped = re.sub(r"[#*\-\s]", "", body)
    templateish = "Movelastweek" in stripped or "Whatyouwrotedownbefore" in stripped
    if templateish and (not canvas_text or len(canvas_text) < 80):
        return False
    return True


def score_week2(row: dict) -> dict:
    submitted = bool(row.get("submitted_at"))
    if not submitted:
        return {
            "score": 0,
            "parts": {"page": 0, "files": 0, "prediction": 0, "result": 0, "limitation": 0, "disclosure": 0},
            "comment": "No Canvas submission by the Tuesday due date.",
            "needs_review": False,
            "reasons": ["unsubmitted"],
        }
    fresh = parse_week2_body(row.get("text") or "")
    for key in ("predicted_mean", "n", "mean_rt", "sd", "has_limitation", "has_disclosure", "names_personalization"):
        if fresh.get(key) and not row.get(key):
            row[key] = fresh[key]
    inspect = row.get("repo_inspect") or {}
    pasted = row.get("pasted_files") or {}
    page_path = inspect.get("page_path") or ""
    note_path = inspect.get("note_path") or ""
    csvs = list(inspect.get("csv_paths") or [])
    if pasted.get("csvs"):
        csvs.extend(p["path"] for p in pasted["csvs"])
    defaultish = inspect.get("page_looks_default")
    named = bool(row.get("names_personalization"))
    strong = bool(STRONG_PERSONAL_RE.search(row.get("text") or ""))
    pasted_page = bool(pasted.get("pages"))
    page_pts = 0
    if strong or (page_path and defaultish is False) or (pasted_page and named):
        page_pts = 2
    elif page_path and named:
        page_pts = 2
    elif page_path or pasted_page:
        page_pts = 1

    note_ok = _note_is_filled(row.get("github_username") or "", note_path, row.get("text") or "")
    if pasted.get("notes"):
        note_ok = True
    files_pts = 2 if note_ok and csvs else (1 if note_ok or csvs else 0)

    pred = str(row.get("predicted_mean") or "")
    if not pred and note_path:
        note = _repo_raw(
            (inspect.get("repo") or ""),
            note_path,
        ) or ""
        m = re.search(r"predict\w*.{0,80}?(\d+(?:\.\d+)?)", note, re.I)
        if m:
            pred = m.group(1)
            row = {**row, "predicted_mean": pred}
        if not row.get("n"):
            n = re.search(r"\bn\s*[=:]\s*(\d+)", note, re.I)
            mean = re.search(r"mean\w*.{0,40}?(\d+(?:\.\d+)?)", note, re.I)
            sd = re.search(r"(?:sd|s\.d\.|stdev|standard deviation).{0,40}?(\d+(?:\.\d+)?)", note, re.I)
            if n:
                row["n"] = n.group(1)
            if mean:
                row["mean_rt"] = mean.group(1)
            if sd:
                row["sd"] = sd.group(1)
        if not row.get("has_limitation"):
            row["has_limitation"] = bool(LIMITATION_RE.search(note))
        if not row.get("has_disclosure"):
            row["has_disclosure"] = bool(DISCLOSURE_RE.search(note))

    pred_pts = 2 if row.get("predicted_mean") else 0
    result_pts = 2 if (row.get("n") and row.get("mean_rt") and row.get("sd")) else (
        1 if (row.get("n") or row.get("mean_rt")) else 0
    )
    lim_pts = 1 if row.get("has_limitation") else 0
    disc_pts = 1 if row.get("has_disclosure") else 0
    parts = {
        "page": page_pts,
        "files": files_pts,
        "prediction": pred_pts,
        "result": result_pts,
        "limitation": lim_pts,
        "disclosure": disc_pts,
    }
    score = sum(parts.values())
    reasons = [
        f"page={page_path or '—'} defaultish={defaultish} named={named} pts={page_pts}",
        f"note={note_path or '—'} csvs={','.join(csvs) or '—'} pts={files_pts}",
        f"pred={row.get('predicted_mean') or '—'} n={row.get('n') or '—'} mean={row.get('mean_rt') or '—'} sd={row.get('sd') or '—'}",
        f"limitation={bool(row.get('has_limitation'))} disclosure={bool(row.get('has_disclosure'))}",
    ]
    comment = (
        f"Week 2: modified RT {parts['page']}, note+CSV {parts['files']}, "
        f"prediction {parts['prediction']}, result {parts['result']}, "
        f"limitation {parts['limitation']}, disclosure {parts['disclosure']}. Total {score}/10."
    )
    review = []
    if page_path and defaultish is True and named and not strong:
        review.append("page still looks like the class default")
    if inspect.get("error"):
        review.append(inspect["error"])
    return {
        "score": score,
        "parts": parts,
        "comment": comment,
        "needs_review": bool(review),
        "reasons": reasons + ([f"review: {'; '.join(review)}"] if review else []),
    }


def _load_json_rows(name: str) -> list[dict]:
    from studio_pipeline import OUT

    path = OUT / name
    if not path.exists():
        raise SystemExit(f"No {name}. Run the matching pull first.")
    return json.loads(path.read_text())


def _write_grades(name: str, rows: list[dict]) -> None:
    from studio_pipeline import OUT

    OUT.mkdir(exist_ok=True)
    (OUT / name).write_text(json.dumps(rows, indent=2) + "\n")


def _grade_week(args, week: int, roster_name: str, score_fn, grades_name: str) -> None:
    from studio_pipeline import _client, _weekly_assignment_id

    try:
        enrolled = current_user_ids()
    except SystemExit:
        enrolled = set()
    week0 = _load_week0_by_id()
    source = _load_json_rows(roster_name)
    client = _client()
    aid = _weekly_assignment_id(client, week)
    plan = []
    for row in source:
        if _skip_row(row):
            continue
        uid = row.get("canvasUserId")
        if uid is not None and enrolled and int(uid) not in enrolled:
            continue
        if not row.get("github_username"):
            row = {**row, "github_username": _username_for(row, week0)}
        scored = score_fn(row)
        item = {
            "canvasUserId": uid,
            "canvasName": row.get("canvasName"),
            "github_username": row.get("github_username"),
            "submitted_at": row.get("submitted_at"),
            "existing_grade": row.get("grade"),
            "existing_score": row.get("score"),
            **scored,
        }
        plan.append(item)
        flag = " REVIEW" if item["needs_review"] else ""
        print(
            f"{item['score']:>4}/10  {uid}\t{item['canvasName']}\t"
            f"{item['comment']}{flag}"
        )
        for reason in item["reasons"]:
            print(f"         {reason}")
    _write_grades(grades_name, plan)
    n = len(plan)
    mean = (sum(p["score"] for p in plan) / n) if n else 0
    submitted = sum(1 for p in plan if p.get("submitted_at"))
    print(f"wrote out/{grades_name}  {n} enrolled  submitted={submitted}  mean={mean:.1f}")

    apply = bool(getattr(args, "apply", False)) and not getattr(args, "dry_run", False)
    if not apply:
        print("dry-run only. Pass --apply to PUT these scores on Canvas.")
        return
    posted = 0
    for item in plan:
        uid = item.get("canvasUserId")
        if uid is None:
            print(f"skip  no canvasUserId  {item.get('canvasName')}")
            continue
        if item.get("existing_score") is not None and not getattr(args, "force", False):
            if float(item["existing_score"]) == float(item["score"]):
                print(f"skip  already {item['score']}  {item['canvasName']}")
                continue
            if not getattr(args, "force", False) and item["existing_score"] not in (None, ""):
                print(
                    f"skip  existing {item['existing_score']} ≠ {item['score']}  "
                    f"{item['canvasName']}  (pass --force to overwrite)"
                )
                continue
        client.grade_submission(aid, str(uid), item["score"], comment=item["comment"])
        print(f"put   {uid}\t{item['score']}\t{item['canvasName']}")
        posted += 1
    print(f"posted {posted} / {n}")


def cmd_week1_grade(args: object) -> None:
    """Score Week 1 from harvested links. Default dry-run."""
    week0 = _load_week0_by_id()
    rows = _load_json_rows("week1_roster.json")
    for row in rows:
        if not row.get("github_username"):
            row["github_username"] = _username_for(row, week0)
    _write_grades("week1_roster.json", rows)
    _grade_week(args, 1, "week1_roster.json", score_week1, "week1_grades.json")


def cmd_week2_grade(args: object) -> None:
    """Score Week 2 from Canvas text + private repo files. Default dry-run."""
    _grade_week(args, 2, "week2_roster.json", score_week2, "week2_grades.json")


WEEK3_DIR = "week03-inventory"
WEEK3_STOP_MARKER = "STOP EDITING HERE"
WEEK3_CSV_HEADER = "item,domain,reverse,response,scored"
TEDIUM_RE = re.compile(
    r"tedi|repetitiv|annoy|boring|painful|error.?prone|time.?consuming|manageable|hand.?edit|editing (ten|10|all)",
    re.I,
)
PREDICTION_RE = re.compile(r"predict|expect|guess|hypothes|i think i", re.I)
ITEM_FIELD_RE = r"""{key}\s*:\s*(?P<q>["'`])(?P<v>(?:\\.|(?!(?P=q)).)*)(?P=q)"""


def _items_block(html: str) -> str:
    start = re.search(r"\bITEMS\s*=\s*\[", html or "")
    if not start:
        return ""
    rest = html[start.end():]
    stop = rest.find(WEEK3_STOP_MARKER)
    if stop >= 0:
        return rest[:stop]
    end = re.search(r"\n\s*\]\s*;", rest)
    return rest[: end.start()] if end else rest[:8000]


def parse_inventory_items(html: str) -> list[dict]:
    """Pull {domain, reverse, text} objects out of a student's ITEMS array."""
    items = []
    for obj in re.finditer(r"\{(.*?)\}", _items_block(html), re.S):
        body = obj.group(1)
        domain = re.search(ITEM_FIELD_RE.format(key="domain"), body, re.S)
        text = re.search(ITEM_FIELD_RE.format(key="text"), body, re.S)
        reverse = re.search(r"reverse\s*:\s*(\d+|true|false)", body, re.I)
        if not text:
            continue
        rev = (reverse.group(1).lower() if reverse else "0")
        items.append(
            {
                "domain": domain.group("v").strip() if domain else "",
                "reverse": 1 if rev in ("1", "true") else 0,
                "text": text.group("v").strip(),
            }
        )
    return items


def _norm_text(value: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", (value or "").lower()).strip()


def _week3_defaults() -> list[str]:
    from studio_pipeline import STUDENT_TEMPLATE

    html = (STUDENT_TEMPLATE / WEEK3_DIR / "inventory.html").read_text(encoding="utf-8")
    return [_norm_text(i["text"]) for i in parse_inventory_items(html)]


def _is_rewritten(text: str, defaults: list[str]) -> bool:
    from difflib import SequenceMatcher

    norm = _norm_text(text)
    if not norm:
        return False
    return all(SequenceMatcher(None, norm, d).ratio() < 0.8 for d in defaults)


def _script_tail(html: str) -> str:
    idx = (html or "").find(WEEK3_STOP_MARKER)
    return re.sub(r"\s+", "", html[idx:]) if idx >= 0 else ""


def _readme_sections(md: str) -> dict[str, str]:
    sections: dict[str, str] = {}
    current = ""
    for line in (md or "").splitlines():
        m = re.match(r"^\s*##(?!#)\s*(.+?)\s*$", line)
        if m:
            current = m.group(1).strip().lower()
            sections[current] = ""
            continue
        if current:
            sections[current] += line + "\n"
    return sections


def _filled_sections(md: str, template_md: str) -> dict[str, str]:
    """Section → student text left after removing the template's prompt lines."""
    template = _readme_sections(template_md)
    out = {}
    for name, body in _readme_sections(md).items():
        prompt = {_norm_text(l) for l in (template.get(name) or "").splitlines() if _norm_text(l)}
        kept = [l for l in body.splitlines() if _norm_text(l) and _norm_text(l) not in prompt]
        text = "\n".join(kept).strip()
        if len(re.findall(r"[A-Za-z0-9]", text)) >= 3:
            out[name] = text
    return out


def _section(filled: dict[str, str], *keys: str) -> str:
    for name, text in filled.items():
        if any(k in name for k in keys):
            return text
    return ""


def _week3_commit_after_due(full: str, due_at: str) -> str:
    """ISO date of the newest week03-inventory commit if it landed after the due date."""
    from studio_pipeline import _gh

    if not due_at:
        return ""
    result = _gh(
        "api",
        f"repos/{full}/commits?path={WEEK3_DIR}&since={due_at}&per_page=1",
        "--jq",
        ".[0].commit.committer.date // empty",
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else ""


def _inspect_week3_repo(full: str, due_at: str = "") -> dict:
    from studio_pipeline import STUDENT_TEMPLATE, _repo_exists, _repo_file_paths

    empty = {"repo": full, "exists": False, "html_path": "", "css_ok": False, "readme_path": "", "csv_paths": []}
    if not full or not _repo_exists(full):
        return empty
    try:
        files = sorted(_repo_file_paths(full))
    except RuntimeError as exc:
        return {**empty, "exists": True, "error": str(exc)[:200]}
    htmls = [p for p in files if p.lower().endswith("inventory.html")]
    html_path = next((p for p in htmls if p.startswith(f"{WEEK3_DIR}/")), htmls[0] if htmls else "")
    folder = html_path.rsplit("/", 1)[0] if "/" in html_path else ""
    prefix = f"{folder}/" if folder else ""
    readme_path = next(
        (p for p in (f"{WEEK3_DIR}/README.md", f"{prefix}README.md") if p in files and p != "README.md"),
        "",
    )
    csv_paths = [
        p
        for p in files
        if p.lower().endswith(".csv") and (p.startswith(f"{WEEK3_DIR}/") or "inventory" in p.lower())
    ]
    html = _repo_raw(full, html_path) if html_path else ""
    script_paths = []
    for src in re.findall(r"""<script[^>]*\bsrc\s*=\s*["']([^"':]+?\.js)["']""", html or "", re.I):
        path = f"{prefix}{src.lstrip('./')}"
        if path in files:
            script_paths.append(path)
            html += "\n" + (_repo_raw(full, path) or "")
    items = parse_inventory_items(html or "")
    defaults = _week3_defaults()
    template_html = (STUDENT_TEMPLATE / WEEK3_DIR / "inventory.html").read_text(encoding="utf-8")
    readme = _repo_raw(full, readme_path) if readme_path else ""
    template_md = (STUDENT_TEMPLATE / WEEK3_DIR / "README.md").read_text(encoding="utf-8")
    csv_header_ok = False
    for path in csv_paths:
        body = _repo_raw(full, path) or ""
        if WEEK3_CSV_HEADER in body[:200]:
            csv_header_ok = True
            break
    domains: dict[str, list[int]] = {}
    for item in items:
        domains.setdefault(item["domain"], []).append(item["reverse"])
    return {
        "repo": full,
        "exists": True,
        "html_path": html_path,
        "script_paths": script_paths,
        "css_ok": f"{prefix}inventory.css" in files,
        "readme_path": readme_path,
        "csv_paths": csv_paths,
        "csv_header_ok": csv_header_ok,
        "items": items,
        "rewritten": sum(1 for i in items if _is_rewritten(i["text"], defaults)),
        "domain_shape": {d: {"n": len(r), "reverse": sum(r)} for d, r in domains.items()},
        "tail_intact": bool(html) and _script_tail(html) == _script_tail(template_html),
        "readme_filled": _filled_sections(readme or "", template_md) if readme else {},
        "late_commit": _week3_commit_after_due(full, due_at),
    }


def cmd_week3_pull(_: object) -> None:
    """Harvest Week 3 Canvas boxes and inspect each private week03-inventory folder. Does not grade."""
    from studio_pipeline import OUT, _client, _plain_text, _repo_full_name, _weekly_assignment_id

    client = _client()
    aid = _weekly_assignment_id(client, 3)
    due_at = (client.get_assignment(aid) or {}).get("due_at") or ""
    week0 = _load_week0_by_id()
    rows = []
    for sub in client.list_submissions(aid):
        user = sub.get("user") or {}
        raw = sub.get("body") or ""
        text = _plain_text(raw)
        row = {
            "canvasUserId": sub.get("user_id"),
            "canvasName": user.get("name"),
            "sortableName": user.get("sortable_name"),
            "sisUserId": user.get("sis_user_id"),
            "workflow": sub.get("workflow_state"),
            "submitted_at": sub.get("submitted_at"),
            "late": bool(sub.get("late")),
            "due_at": due_at,
            "grade": sub.get("grade"),
            "score": sub.get("score"),
            "github_username": _username_for({"canvasUserId": sub.get("user_id")}, week0),
            "text": text[:4000],
            "urls": parse_week2_body(raw).get("urls") or [],
        }
        if _skip_row(row):
            continue
        own = _repo_full_name(row["github_username"]) if row["github_username"] else ""
        inspect = _inspect_week3_repo(own, due_at) if own else {"repo": None, "exists": False}
        if not inspect.get("html_path"):
            for url in row["urls"]:
                if CLASS_DEMO_RE.search(url):
                    continue
                m = BLOB_RE.search(url) or re.search(r"github\.com/([^/]+)/([^/?#]+)", url, re.I)
                if not m:
                    continue
                other = f"{m.group(1)}/{m.group(2).removesuffix('.git')}"
                if other.lower() == (own or "").lower():
                    continue
                alt = _inspect_week3_repo(other, due_at)
                if alt.get("html_path"):
                    inspect = {**alt, "not_own_repo": True}
                    break
        row["repo_inspect"] = inspect
        rows.append(row)
    OUT.mkdir(exist_ok=True)
    dest = OUT / "week3_roster.json"
    dest.write_text(json.dumps(rows, indent=2) + "\n")
    submitted = [r for r in rows if r.get("submitted_at")]
    pages = [r for r in submitted if (r.get("repo_inspect") or {}).get("html_path")]
    full = [r for r in submitted if (r.get("repo_inspect") or {}).get("rewritten") == 10]
    notes = [r for r in submitted if (r.get("repo_inspect") or {}).get("readme_path")]
    csvs = [r for r in submitted if (r.get("repo_inspect") or {}).get("csv_paths")]
    print(
        f"wrote {dest}  {len(submitted)} submitted / {len(rows)} rows  "
        f"pages={len(pages)} all-ten-rewritten={len(full)} notes={len(notes)} csvs={len(csvs)}"
    )


def score_week3(row: dict) -> dict:
    zero = {"items": 0, "structure": 0, "files": 0, "prediction": 0, "tedium": 0, "disclosure": 0}
    if not row.get("submitted_at"):
        return {
            "score": 0,
            "parts": zero,
            "comment": "No Canvas submission by the Tuesday due date.",
            "needs_review": False,
            "reasons": ["unsubmitted"],
        }
    inspect = row.get("repo_inspect") or {}
    text = row.get("text") or ""
    filled = inspect.get("readme_filled") or {}
    items = inspect.get("items") or []
    rewritten = int(inspect.get("rewritten") or 0)
    review = []

    if rewritten >= 10:
        items_pts = 3
    elif rewritten >= 5:
        items_pts = 2
    elif rewritten >= 1:
        items_pts = 1
    else:
        items_pts = 0
    if 0 < rewritten < 10:
        review.append(f"{rewritten}/10 items rewritten")

    shape = inspect.get("domain_shape") or {}
    shape_ok = (
        len(items) == 10
        and len(shape) == 5
        and all(v["n"] == 2 and v["reverse"] == 1 for v in shape.values())
    )
    css_ok = bool(inspect.get("css_ok"))
    tail_ok = bool(inspect.get("tail_intact"))
    if not inspect.get("html_path"):
        struct_pts = 0
    elif shape_ok and css_ok:
        struct_pts = 2
    else:
        struct_pts = 1
    if inspect.get("html_path") and not tail_ok:
        review.append("scoring code below STOP EDITING differs from the template")

    readme_ok = bool(inspect.get("readme_path")) and bool(filled)
    csv_ok = bool(inspect.get("csv_paths"))
    files_pts = (1 if readme_ok else 0) + (1 if csv_ok else 0)
    if csv_ok and not inspect.get("csv_header_ok"):
        review.append("CSV header is not the inventory export")
    if csv_ok and not any(p.startswith(f"{WEEK3_DIR}/") for p in inspect.get("csv_paths") or []):
        review.append("CSV is outside week03-inventory/")

    pred = _section(filled, "predict")
    pred_pts = 1 if (pred or PREDICTION_RE.search(text)) else 0
    tedium = _section(filled, "tedium")
    tedium_pts = 1 if (tedium or TEDIUM_RE.search(text)) else 0
    disclosure = _section(filled, "disclosure", "copilot")
    disc_pts = 1 if (disclosure or DISCLOSURE_RE.search(text)) else 0

    if inspect.get("not_own_repo"):
        review.append(f"graded from pasted repo {inspect.get('repo')}")
    if inspect.get("error"):
        review.append(inspect["error"])
    if row.get("late"):
        review.append("Canvas marks the submission late")
    if inspect.get("late_commit"):
        review.append(f"week03-inventory commit after due: {inspect['late_commit']}")

    parts = {
        "items": items_pts,
        "structure": struct_pts,
        "files": files_pts,
        "prediction": pred_pts,
        "tedium": tedium_pts,
        "disclosure": disc_pts,
    }
    score = sum(parts.values())
    shape_txt = ",".join(f"{d}:{v['n']}/{v['reverse']}r" for d, v in shape.items()) or "—"
    reasons = [
        f"html={inspect.get('html_path') or '—'} scripts={','.join(inspect.get('script_paths') or []) or '—'} "
        f"rewritten={rewritten}/{len(items)} pts={items_pts}",
        f"shape={shape_txt} css={css_ok} tail={tail_ok} pts={struct_pts}",
        f"readme={inspect.get('readme_path') or '—'} filled={','.join(filled) or '—'} csvs={','.join(inspect.get('csv_paths') or []) or '—'} pts={files_pts}",
        f"prediction={pred_pts} tedium={tedium_pts} disclosure={disc_pts}",
    ]
    comment = (
        f"Week 3: items rewritten {parts['items']}, structure {parts['structure']}, "
        f"note+CSV {parts['files']}, prediction {parts['prediction']}, "
        f"tedium {parts['tedium']}, disclosure {parts['disclosure']}. Total {score}/10."
    )
    return {
        "score": score,
        "parts": parts,
        "comment": comment,
        "needs_review": bool(review),
        "reasons": reasons + ([f"review: {'; '.join(review)}"] if review else []),
    }


WEEK3_STYLE_BONUS = 0.5


def _load_week3_bonus() -> dict[int, str]:
    """Instructor-confirmed style bonus: out/week3_bonus.json maps canvasUserId → what changed."""
    from studio_pipeline import OUT

    path = OUT / "week3_bonus.json"
    if not path.exists():
        return {}
    return {int(k): v for k, v in json.loads(path.read_text()).items()}


def cmd_week3_grade(args: object) -> None:
    """Score Week 3 from Canvas text + private week03-inventory files. Default dry-run."""
    bonus = _load_week3_bonus()

    def score(row: dict) -> dict:
        scored = score_week3(row)
        what = bonus.get(int(row["canvasUserId"])) if row.get("canvasUserId") is not None else None
        if what and row.get("submitted_at"):
            scored["score"] = scored["score"] + WEEK3_STYLE_BONUS
            scored["parts"]["style_bonus"] = WEEK3_STYLE_BONUS
            scored["comment"] += f" Style bonus +{WEEK3_STYLE_BONUS} ({what}). Final {scored['score']}."
            scored["reasons"].append(f"style bonus: {what}")
        return scored

    _grade_week(args, 3, "week3_roster.json", score, "week3_grades.json")


def _list_studio_repos() -> list[str]:
    from studio_pipeline import GITHUB_OWNER, _gh

    result = _gh("repo", "list", GITHUB_OWNER, "--limit", "200", "--json", "name,isArchived")
    rows = json.loads(result.stdout)
    out = []
    for row in rows:
        name = row.get("name") or ""
        if not name.lower().startswith("psych302-305-"):
            continue
        if name.lower() == "psych302-305-kylemathewson":
            continue
        out.append({"name": name, "archived": bool(row.get("isArchived"))})
    return out


def _norm_token(value: str) -> str:
    return re.sub(r"[^a-z0-9]", "", (value or "").lower())


def _name_matches_username(fullname: str, username: str) -> bool:
    n = _norm_token(fullname)
    u = _norm_token(username)
    if not n or not u:
        return False
    if u in n or n in u:
        return True
    tokens = [t for t in re.findall(r"[a-z]+", fullname.lower()) if len(t) >= 5]
    return any(t in u for t in tokens)


def _match_people(people: list[dict], username: str) -> list[dict]:
    exact: list[dict] = []
    fuzzy: list[dict] = []
    for row in people:
        resolved = _username_for(row, {int(row["canvasUserId"]): row} if row.get("canvasUserId") is not None else {})
        raw = (row.get("github_username") or "").strip()
        if (resolved and resolved.lower() == username.lower()) or (raw and raw.lower() == username.lower()):
            exact.append(row)
        elif _name_matches_username(row.get("canvasName") or "", username):
            fuzzy.append(row)
    return exact or fuzzy


def build_cleanup_plan() -> list[dict]:
    from studio_pipeline import GITHUB_OWNER, OUT

    roster = load_roster()
    enrolled = current_user_ids(roster)
    week0 = _load_week0_by_id()
    current_people = []
    for row in roster.get("current") or []:
        extra = week0.get(int(row["canvasUserId"])) if row.get("canvasUserId") is not None else None
        current_people.append({**row, **(extra or {})})
    former_people = list(roster.get("former") or [])
    plan = []
    for repo in _list_studio_repos():
        name = repo["name"]
        username = name[len("psych302-305-") :]
        if username.lower() in KEEP_USERNAMES:
            plan.append(
                {
                    "repo": f"{GITHUB_OWNER}/{name}",
                    "github_username": username,
                    "action": "keep-demo",
                    "reason": "instructor demo",
                    "archived": repo["archived"],
                    "canvasName": "Kyle Mathewson",
                }
            )
            continue
        active = _match_people(current_people, username)
        former = _match_people(former_people, username)
        if active:
            action, reason = "keep", "owner still enrolled"
            who = active[0]
        elif former:
            action, reason = "archive", "name/username matches a student no longer enrolled"
            who = former[0]
        else:
            action, reason = "review", "no current or former student match; will not archive"
            who = {}
        plan.append(
            {
                "repo": f"{GITHUB_OWNER}/{name}",
                "github_username": username,
                "action": action,
                "reason": reason,
                "archived": repo["archived"],
                "canvasUserId": who.get("canvasUserId"),
                "canvasName": who.get("canvasName"),
            }
        )
    dest = OUT / "cleanup_plan.json"
    dest.write_text(json.dumps(plan, indent=2) + "\n")
    return plan


def cmd_repos_cleanup(args: object) -> None:
    """Archive private studio repos whose week0 owner is no longer enrolled. Default dry-run."""
    from studio_pipeline import _gh

    plan = build_cleanup_plan()
    counts: dict[str, int] = {}
    for item in plan:
        counts[item["action"]] = counts.get(item["action"], 0) + 1
        print(
            f"{item['action']:<12} {item['repo']}\t{item.get('canvasName') or '—'}\t"
            f"{item['reason']}" + (" (already archived)" if item.get("archived") else "")
        )
    print("plan  " + "  ".join(f"{k}={v}" for k, v in sorted(counts.items())))
    apply = bool(getattr(args, "apply", False)) and not getattr(args, "dry_run", False)
    if not apply:
        print("dry-run only. Pass --apply to archive action=archive repos. This does not delete.")
        return
    n = 0
    for item in plan:
        if item["action"] != "archive":
            continue
        if item.get("archived"):
            print(f"already-archived         {item['repo']}")
            continue
        result = _gh("repo", "archive", item["repo"], "--yes", check=False)
        if result.returncode != 0:
            print(f"error                    {item['repo']}\t{(result.stderr or result.stdout)[:300]}")
            continue
        print(f"archived                 {item['repo']}\t{item.get('canvasName')}")
        n += 1
    print(f"archived {n} repo(s)")
