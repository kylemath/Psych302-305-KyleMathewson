#!/usr/bin/env python3
"""Week 7 Part 2: reanalyse the Stroop data from Hedge, Powell & Sumner (2018).

Hedge, C., Powell, G., & Sumner, P. (2018). The reliability paradox: Why robust
cognitive tasks do not produce reliable individual differences. Behavior
Research Methods, 50(3), 1166-1186. https://doi.org/10.3758/s13428-017-0935-1
Data: https://osf.io/cwzds/ (tidied into one CSV on the course site).

Run from week07-methods/ (the Week 4 virtual environment works; matplotlib is
only needed for the figures):

    python3 analyze_stroop.py
    python3 analyze_stroop.py --mine stroop-week07.csv
    python3 analyze_stroop.py --mine stroop-week07.csv --rule course

The first run downloads hedge2018-stroop.csv into this folder.
"""

from __future__ import annotations

import argparse
import csv
import statistics
import urllib.request
from collections import defaultdict
from pathlib import Path

DATA_URL = "https://kylemath.github.io/Psych302-305-KyleMathewson/data/hedge2018-stroop.csv"
LOCAL = Path("hedge2018-stroop.csv")
MIN_ACCURACY = 0.60


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Stroop effect and test-retest reliability, Hedge et al. (2018).")
    parser.add_argument("--hedge", type=Path, default=LOCAL, help="Path to hedge2018-stroop.csv")
    parser.add_argument("--mine", type=Path, help="Your own Stroop CSV (columns: condition, rt, correct)")
    parser.add_argument(
        "--rule",
        choices=["hedge", "course"],
        default="hedge",
        help="hedge: drop RT < 100 ms and RT more than 3 MADs from the median; course: keep 150-2500 ms",
    )
    parser.add_argument("--out", type=Path, default=Path("output"), help="Folder for numbers.md and figures")
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(newline="", encoding="utf-8") as handle:
        return [{k.strip(): (v or "").strip() for k, v in row.items()} for row in csv.DictReader(handle)]


def fetch_hedge(path: Path) -> None:
    if path.exists():
        return
    print(f"Downloading {DATA_URL} ...")
    urllib.request.urlretrieve(DATA_URL, path)


def keep_rts(rts: list[float], rule: str) -> list[float]:
    """Apply the trimming rule to one person's correct RTs in one condition."""
    if rule == "course":
        return [rt for rt in rts if 150 <= rt <= 2500]
    rts = [rt for rt in rts if rt >= 100]
    if len(rts) < 3:
        return rts
    med = statistics.median(rts)
    mad = statistics.median(abs(rt - med) for rt in rts)
    # The paper says "three times each individual's median absolute deviation".
    # Here that is read as: per person, per session, per condition. Is that what they did?
    return [rt for rt in rts if abs(rt - med) <= 3 * mad]


def person_means(rows: list[dict[str, str]], rule: str) -> dict:
    """Return {(study, participant, session): {"accuracy": a, "congruent": m, "incongruent": m}}."""
    rts = defaultdict(list)
    hits = defaultdict(int)
    counts = defaultdict(int)
    for row in rows:
        if row["condition"] not in ("congruent", "incongruent", "neutral"):
            continue
        key = (row["study"], row["participant"], row["session"])
        counts[key] += 1
        if row["correct"] == "1":
            hits[key] += 1
            rts[key + (row["condition"],)].append(float(row["rt_ms"]))
    out = {}
    for key, n in counts.items():
        cell = {"accuracy": hits[key] / n}
        for condition in ("congruent", "incongruent"):
            kept = keep_rts(rts.get(key + (condition,), []), rule)
            cell[condition] = statistics.mean(kept) if kept else None
        out[key] = cell
    return out


def pearson(xs: list[float], ys: list[float]) -> float:
    mx, my = statistics.mean(xs), statistics.mean(ys)
    sxy = sum((x - mx) * (y - my) for x, y in zip(xs, ys))
    sxx = sum((x - mx) ** 2 for x in xs)
    syy = sum((y - my) ** 2 for y in ys)
    return sxy / (sxx * syy) ** 0.5


def my_effect(path: Path, rule: str) -> tuple[float, float, int]:
    rows = read_csv(path)
    rt_col = "rt" if "rt" in rows[0] else "rt_ms"
    rows = [r for r in rows if r.get("practice", "0") != "1"]
    means = {}
    n = 0
    for condition in ("congruent", "incongruent"):
        rts = [float(r[rt_col]) for r in rows if r["condition"] == condition and r.get("correct", "1") == "1"]
        kept = keep_rts(rts, rule)
        if not kept:
            raise SystemExit(f"No usable {condition} trials in {path}. Check the condition and correct columns.")
        means[condition] = statistics.mean(kept)
        n += len(kept)
    return means["congruent"], means["incongruent"], n


def draw_figures(out: Path, effects_s1: list[float], pairs: list[tuple[float, float]], mine: float | None) -> list[str]:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("matplotlib is missing, so no figures. pip install matplotlib")
        return []
    out.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    ax.hist(effects_s1, bins=20, color="#c4a574", edgecolor="#1c1915")
    if mine is not None:
        ax.axvline(mine, color="#1c1915", linestyle="--", linewidth=1.4, label=f"me = {mine:.0f} ms")
        ax.legend(frameon=False)
    ax.set_xlabel("Stroop effect, session 1 (incongruent - congruent, ms)")
    ax.set_ylabel("Participants")
    fig.tight_layout()
    fig.savefig(out / "effects.png", dpi=150)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(4.2, 4.2))
    ax.scatter([a for a, _ in pairs], [b for _, b in pairs], color="#c4a574", edgecolor="#1c1915")
    lo = min(min(p) for p in pairs)
    hi = max(max(p) for p in pairs)
    ax.plot([lo, hi], [lo, hi], color="#1c1915", linewidth=0.8, linestyle=":")
    ax.set_xlabel("Stroop effect, session 1 (ms)")
    ax.set_ylabel("Stroop effect, session 2 (ms)")
    fig.tight_layout()
    fig.savefig(out / "retest.png", dpi=150)
    plt.close(fig)
    return ["effects.png", "retest.png"]


def main() -> None:
    args = parse_args()
    fetch_hedge(args.hedge)
    cells = person_means(read_csv(args.hedge), args.rule)

    people = {(s, p) for s, p, _ in cells}
    kept_people = sorted(
        (s, p)
        for s, p in people
        if all(
            (s, p, sess) in cells
            and cells[(s, p, sess)]["accuracy"] >= MIN_ACCURACY
            and None not in (cells[(s, p, sess)]["congruent"], cells[(s, p, sess)]["incongruent"])
            for sess in ("1", "2")
        )
    )
    dropped = len(people) - len(kept_people)

    lines = [f"Rule: `{args.rule}`. Participants: {len(kept_people)} kept, {dropped} excluded "
             f"(missing a session or accuracy under {MIN_ACCURACY:.0%}).", ""]
    lines.append("| Session | Congruent (ms) | Incongruent (ms) | Stroop effect (ms) | Effect > 0 |")
    lines.append("| --- | --- | --- | --- | --- |")
    effects = {}
    rts = {}
    for sess in ("1", "2"):
        con = [cells[(s, p, sess)]["congruent"] for s, p in kept_people]
        inc = [cells[(s, p, sess)]["incongruent"] for s, p in kept_people]
        effects[sess] = [i - c for c, i in zip(con, inc)]
        rts[sess] = con
        positive = sum(1 for e in effects[sess] if e > 0)
        lines.append(
            f"| {sess} | {statistics.mean(con):.0f} | {statistics.mean(inc):.0f} | "
            f"{statistics.mean(effects[sess]):.0f} (SD {statistics.stdev(effects[sess]):.0f}) | "
            f"{positive} of {len(kept_people)} |"
        )
    r_effect = pearson(effects["1"], effects["2"])
    r_rt = pearson(rts["1"], rts["2"])
    lines += [
        "",
        f"Session 1 vs session 2, same people three weeks apart (Pearson r):",
        f"- Stroop effect: r = {r_effect:.2f}",
        f"- Plain congruent RT: r = {r_rt:.2f}",
        "",
        "The paper reports ICCs, not Pearson r, so expect close but not identical numbers.",
    ]

    mine = None
    if args.mine:
        con, inc, n = my_effect(args.mine, args.rule)
        mine = inc - con
        below = sum(1 for e in effects["1"] if e < mine)
        lines += [
            "",
            f"Me (`{args.mine.name}`, {n} usable correct trials): congruent {con:.0f} ms, "
            f"incongruent {inc:.0f} ms, Stroop effect {mine:.0f} ms. "
            f"That is larger than {below} of {len(effects['1'])} Hedge participants in session 1.",
        ]

    figures = draw_figures(args.out, effects["1"], list(zip(effects["1"], effects["2"])), mine)
    if figures:
        lines += ["", "Figures: " + ", ".join(f"`output/{name}`" for name in figures)]

    text = "\n".join(lines) + "\n"
    args.out.mkdir(parents=True, exist_ok=True)
    (args.out / "numbers.md").write_text(text, encoding="utf-8")
    print(text)
    print(f"wrote {args.out / 'numbers.md'}")


if __name__ == "__main__":
    main()
