#!/usr/bin/env python3
"""Read a Week 2 RT or Week 3 inventory CSV, write numbers, and draw a figure.

Run from this folder (e.g. week04-report/) inside the local virtual environment:

    python3 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python scripts/summarize.py --csv yourfile.csv
    python scripts/summarize.py --csv ../week02-rt/yourfile.csv
"""

from __future__ import annotations

import argparse
import json
import statistics
from pathlib import Path

RT_MIN = 150.0
RT_MAX = 2500.0
INV_MIN = 1.0
INV_MAX = 5.0


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate report numbers and a figure from a CSV.")
    parser.add_argument("--csv", required=True, type=Path, help="Path to a reaction-time or inventory CSV")
    parser.add_argument("--out", type=Path, default=Path("output"), help="Directory for generated snippets")
    parser.add_argument("--report", type=Path, default=Path("README.md"), help="Markdown file with generated markers")
    return parser.parse_args()


def read_rows(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    import csv

    with path.open(newline="", encoding="utf-8") as handle:
        lines = [line for line in handle if line.strip() and not line.lstrip().startswith("#")]
    reader = csv.DictReader(lines)
    if reader.fieldnames is None:
        raise SystemExit(f"No header row in {path}")
    headers = [name.strip() for name in reader.fieldnames]
    rows = []
    for raw in reader:
        rows.append({key.strip(): (raw.get(key) or "").strip() for key in reader.fieldnames})
    return headers, rows


def detect_kind(headers: list[str]) -> str:
    names = {name.lower() for name in headers}
    if "rt" in names:
        return "rt"
    if "scored" in names:
        return "inventory"
    return "numeric"


def first_numeric_column(headers: list[str], rows: list[dict[str, str]]) -> str:
    for name in headers:
        for row in rows:
            try:
                float(row[name])
                return name
            except ValueError:
                continue
    raise SystemExit("No numeric column found.")


def usable_values(kind: str, headers: list[str], rows: list[dict[str, str]]) -> tuple[str, float, float, list[float]]:
    if kind == "rt":
        column = next(name for name in headers if name.lower() == "rt")
        low, high = RT_MIN, RT_MAX
    elif kind == "inventory":
        column = next(name for name in headers if name.lower() == "scored")
        low, high = INV_MIN, INV_MAX
    else:
        column = first_numeric_column(headers, rows)
        low, high = float("-inf"), float("inf")
    values: list[float] = []
    for row in rows:
        try:
            value = float(row[column])
        except ValueError:
            continue
        if low <= value <= high:
            values.append(value)
    return column, low, high, values


def format_mean(value: float, kind: str) -> str:
    if kind == "rt":
        return f"{value:.0f} ms"
    return f"{value:.2f}"


def typst_raw(text: str) -> str:
    return "#raw(" + json.dumps(text) + ")"


def write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


def splice_report(path: Path, body: str) -> None:
    if not path.exists():
        return
    start = "<!-- begin generated -->"
    end = "<!-- end generated -->"
    text = path.read_text(encoding="utf-8")
    if start not in text or end not in text:
        return
    before, rest = text.split(start, 1)
    _, after = rest.split(end, 1)
    path.write_text(f"{before}{start}\n{body.rstrip()}\n{end}{after}", encoding="utf-8")


def write_figure(path: Path, values: list[float], kind: str, mean_value: float) -> str:
    try:
        import matplotlib

        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        raise SystemExit(
            "matplotlib is missing. From week04-report/: python3 -m venv .venv && "
            "source .venv/bin/activate && pip install -r requirements.txt"
        )

    path.parent.mkdir(parents=True, exist_ok=True)
    fig, ax = plt.subplots(figsize=(6.2, 3.6))
    if kind == "rt":
        bins = min(12, max(5, len(values) // 2 or 5))
        ax.hist(values, bins=bins, color="#c4a574", edgecolor="#1c1915")
        ax.axvline(mean_value, color="#1c1915", linestyle="--", linewidth=1.2, label=f"mean = {mean_value:.0f} ms")
        ax.set_xlabel("Reaction time (ms)")
        caption = "Distribution of usable reaction times. The dashed line is the mean."
    elif kind == "inventory":
        scores = [1, 2, 3, 4, 5]
        counts = [sum(1 for value in values if int(round(value)) == score) for score in scores]
        ax.bar(scores, counts, color="#c4a574", edgecolor="#1c1915")
        ax.set_xticks(scores)
        ax.set_xlabel("Scored response")
        caption = "Counts of usable inventory item scores after reverse scoring."
    else:
        bins = min(12, max(5, len(values) // 2 or 5))
        ax.hist(values, bins=bins, color="#c4a574", edgecolor="#1c1915")
        ax.axvline(mean_value, color="#1c1915", linestyle="--", linewidth=1.2, label=f"mean = {mean_value:.2f}")
        ax.set_xlabel("Value")
        caption = "Distribution of usable values. The dashed line is the mean."
    ax.set_ylabel("Count")
    if kind != "inventory":
        ax.legend(frameon=False)
    fig.tight_layout()
    fig.savefig(path, dpi=150)
    plt.close(fig)
    return caption


def main() -> None:
    args = parse_args()
    if not args.csv.exists():
        raise SystemExit(f"CSV not found: {args.csv}")
    headers, rows = read_rows(args.csv)
    kind = detect_kind(headers)
    column, low, high, values = usable_values(kind, headers, rows)
    n = len(values)
    if n == 0:
        raise SystemExit("No usable values after exclusion. Check the file and the range.")
    mean = statistics.mean(values)
    sd = statistics.stdev(values) if n > 1 else None
    excluded = len(rows) - n
    mean_text = format_mean(mean, kind)
    sd_text = format_mean(sd, kind) if sd is not None else None
    if kind == "rt":
        label = "reaction time"
        range_text = f"times under {low:.0f} ms or over {high:.0f} ms were excluded"
    elif kind == "inventory":
        label = "inventory item scores"
        range_text = f"scores outside {low:.0f}–{high:.0f} were excluded"
    else:
        label = f"column `{column}`"
        range_text = "no default exclusion range"
    figure_path = args.out / "figure.png"
    caption = write_figure(figure_path, values, kind, mean)
    md = (
        f"File `{args.csv.name}`: {n} usable values of {label} "
        f"(column `{column}`). Mean = {mean_text}"
        + (f", SD = {sd_text}" if sd_text is not None else "")
        + f". {excluded} row(s) excluded; {range_text}. "
        f"Figure: `{figure_path.name}`.\n"
    )
    typ_mean = f"{mean:.0f}" if kind == "rt" else f"{mean:.2f}"
    typ_sd = None if sd is None else (f"{sd:.0f}" if kind == "rt" else f"{sd:.2f}")
    unit = " ms" if kind == "rt" else ""
    sd_clause = f", SD = ${typ_sd}${unit}" if typ_sd is not None else ""
    table_sd = f"{typ_sd}{unit}" if typ_sd is not None else "—"
    typ = (
        f"File {typst_raw(args.csv.name)}: $n={n}$ usable values of {label} "
        f"(column {typst_raw(column)}). Mean = ${typ_mean}${unit}{sd_clause}. "
        f"{excluded} row(s) excluded; {range_text}.\n\n"
        f"#table(\n"
        f"  columns: (auto, auto),\n"
        f"  inset: 6pt,\n"
        f"  stroke: 0.4pt,\n"
        f"  [*Statistic*], [*Value*],\n"
        f"  [$n$], [{n}],\n"
        f"  [Mean], [{typ_mean}{unit}],\n"
        f"  [SD], [{table_sd}],\n"
        f"  [Excluded], [{excluded}],\n"
        f")\n\n"
        f"#figure(\n"
        f"  image({json.dumps(figure_path.name)}, width: 90%),\n"
        f"  caption: [{caption}],\n"
        f")\n"
    )
    args.out.mkdir(parents=True, exist_ok=True)
    write_text(args.out / "numbers.md", md)
    write_text(args.out / "numbers.typ", typ)
    splice_report(args.report, md)
    print(md.rstrip())
    print(f"wrote {args.out / 'numbers.md'}")
    print(f"wrote {args.out / 'numbers.typ'}")
    print(f"wrote {figure_path}")
    if args.report.exists():
        print(f"updated {args.report} between generated markers")


if __name__ == "__main__":
    main()
