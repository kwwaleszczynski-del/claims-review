#!/usr/bin/env python3
"""List every number in a README and say whether a results file backs it.

For each number found in the README the script looks for a value in the
results files (JSON and CSV under the results directory) that equals it once
rounded to the precision the README prints. A percentage also matches a stored
fraction (90% matches 0.9). Signs are ignored ("cut by 12%" matches -0.12).

Statuses:
  traced    a results value rounds to this number
  near      a results value is within one unit of the last printed digit
            (truncation, or a number that drifted since it was typed)
  UNTRACED  nothing in the results files backs this number
  minor     untraced bare integer <= 12 (counts, list sizes); not flagged
  skipped   untraced and looks like a calendar year

A traced number is not a verified number: it only means the README agrees with
the results file. An untraced number is not wrong either: it may be derived
(a difference, a ratio) or typed by hand. Both facts go to the reviewer.

Usage:
    python trace_numbers.py path/to/repo
    python trace_numbers.py path/to/repo --readme README.md --readme docs/results.md
    python trace_numbers.py path/to/repo --results results --results out --json
    python trace_numbers.py path/to/repo --include-code

Standard library only. Exit code is 0 unless the README cannot be read.
"""

import argparse
import csv
import json
import math
import re
import sys
from pathlib import Path

FENCE = re.compile(r"^\s*(```|~~~)")
MASKS = [
    re.compile(r"https?://\S+"),
    re.compile(r"\]\([^)]*\)"),                        # markdown link targets
    re.compile(r"\b\d{4}-\d{2}(?:-\d{2})?\b"),         # ISO dates and months
    re.compile(r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b"),  # other dates
    re.compile(r"\b\d{1,2}:\d{2}(?::\d{2})?\b"),       # clock times
    re.compile(r"\bv?\d+\.\d+\.\d+(?:\.\d+)*\b"),      # version strings
    re.compile(r"^\s*(?:#+\s*)?\d+[.)]\s"),            # list and heading ordinals
]
NUMBER = re.compile(
    r"(?<![\w.,/:])(?P<sign>[-−](?=\d))?"
    r"(?P<num>\d{1,3}(?:,\d{3})+(?:\.\d+)?|\d+(?:\.\d+)?)"
    r"(?P<pct>\s?%|\s?percent\b)?"
    r"(?![.,:/]?\d)"
)
MAX_SOURCES = 3


def _mask(line):
    for pattern in MASKS:
        line = pattern.sub(lambda m: " " * len(m.group()), line)
    return line


def extract_numbers(text, include_code=False):
    """Return a list of dicts: line, text, value, decimals, percent."""
    found = []
    in_fence = False
    for lineno, line in enumerate(text.splitlines(), start=1):
        if FENCE.match(line):
            in_fence = not in_fence
            continue
        if in_fence and not include_code:
            continue
        for m in NUMBER.finditer(_mask(line)):
            digits = m.group("num").replace(",", "")
            value = float(digits)
            if m.group("sign"):
                value = -value
            found.append({
                "line": lineno,
                "text": m.group().strip(),
                "value": value,
                "decimals": len(digits.split(".")[1]) if "." in digits else 0,
                "percent": bool(m.group("pct")),
            })
    return found


def _as_number(obj):
    if isinstance(obj, bool):
        return None
    if isinstance(obj, (int, float)):
        value = float(obj)
    elif isinstance(obj, str):
        try:
            value = float(obj.strip().rstrip("%"))
        except ValueError:
            return None
    else:
        return None
    return value if math.isfinite(value) else None


def _walk_json(obj, path, source, out):
    if isinstance(obj, dict):
        for key, child in obj.items():
            _walk_json(child, f"{path}.{key}" if path else str(key), source, out)
    elif isinstance(obj, list):
        for i, child in enumerate(obj):
            _walk_json(child, f"{path}[{i}]", source, out)
    else:
        value = _as_number(obj)
        if value is not None:
            out.append((value, f"{source}:{path}"))


def collect_results(repo, results_dirs):
    """Return (values, files): values is a list of (float, 'file:location')."""
    values, files = [], []
    for results_dir in results_dirs:
        base = Path(repo) / results_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            suffix = path.suffix.lower()
            if suffix not in (".json", ".csv") or not path.is_file():
                continue
            source = path.relative_to(repo).as_posix()
            try:
                if suffix == ".json":
                    with open(path, encoding="utf-8-sig") as fh:
                        _walk_json(json.load(fh), "", source, values)
                else:
                    with open(path, encoding="utf-8-sig", newline="") as fh:
                        rows = list(csv.reader(fh))
                    header = rows[0] if rows else []
                    for r, row in enumerate(rows[1:], start=2):
                        for c, cell in enumerate(row):
                            value = _as_number(cell)
                            if value is not None:
                                col = header[c] if c < len(header) else f"col{c + 1}"
                                values.append((value, f"{source}:row {r}:{col}"))
            except (OSError, ValueError) as exc:
                print(f"warning: could not read {source}: {exc}", file=sys.stderr)
                continue
            files.append(source)
    return values, files


def trace(number, values):
    """Classify one README number against the results values."""
    target = abs(number["value"])
    unit = 10.0 ** -number["decimals"]
    scales = (1.0, 100.0) if number["percent"] else (1.0,)
    small_int = (number["decimals"] == 0 and not number["percent"] and target <= 12)
    exact, near = [], []
    for value, where in values:
        for scale in scales:
            diff = abs(abs(value * scale) - target)
            if small_int:
                # a bare small integer only matches the same integer
                if diff < 1e-9:
                    exact.append((value, where))
            elif diff <= unit / 2 + unit * 1e-6:
                exact.append((value, where))
            elif diff <= unit * (1 + 1e-6):
                near.append((value, where))
    if exact:
        status, sources = "traced", exact
    elif near:
        status, sources = "near", near
    elif small_int:
        status, sources = "minor", []
    elif number["decimals"] == 0 and not number["percent"] and 1900 <= target <= 2100:
        status, sources = "skipped", []
    else:
        status, sources = "UNTRACED", []
    seen, unique = set(), []
    for value, where in sources:
        if where not in seen:
            seen.add(where)
            unique.append({"value": value, "where": where})
    return {**number, "status": status, "n_sources": len(unique),
            "sources": unique[:MAX_SOURCES]}


def run(repo, readmes=("README.md",), results_dirs=("results",), include_code=False):
    repo = Path(repo)
    values, files = collect_results(repo, results_dirs)
    rows = []
    for readme in readmes:
        text = (repo / readme).read_text(encoding="utf-8-sig")
        for number in extract_numbers(text, include_code=include_code):
            rows.append({"file": Path(readme).as_posix(), **trace(number, values)})
    counts = {}
    for row in rows:
        counts[row["status"]] = counts.get(row["status"], 0) + 1
    return {"results_files": files, "n_result_values": len(values),
            "counts": counts, "numbers": rows}


def format_text(report):
    lines = []
    if not report["results_files"]:
        lines.append("No results files found: every number is untraceable by this "
                     "script. Ask where the README numbers come from.")
    else:
        lines.append(f"Results files: {len(report['results_files'])} "
                     f"({report['n_result_values']} numeric values)")
    counts = report["counts"]
    order = ["traced", "near", "UNTRACED", "minor", "skipped"]
    lines.append(f"README numbers: {len(report['numbers'])} | "
                 + " | ".join(f"{counts.get(s, 0)} {s}" for s in order))
    lines.append("")
    lines.append(f"{'file:line':<22} {'number':<12} {'status':<9} source")
    for row in report["numbers"]:
        if row["sources"]:
            first = row["sources"][0]
            source = f"{first['where']} = {first['value']:g}"
            if row["n_sources"] > 1:
                source += f"  (+{row['n_sources'] - 1} more)"
        else:
            source = "-"
        lines.append(f"{row['file'] + ':' + str(row['line']):<22} "
                     f"{row['text']:<12} {row['status']:<9} {source}")
    return "\n".join(lines)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Trace README numbers to values in results files.")
    parser.add_argument("repo", help="path to the repository under review")
    parser.add_argument("--readme", action="append",
                        help="markdown file relative to the repo (repeatable; "
                             "default README.md)")
    parser.add_argument("--results", action="append",
                        help="results directory relative to the repo (repeatable; "
                             "default results)")
    parser.add_argument("--include-code", action="store_true",
                        help="also read numbers inside fenced code blocks")
    parser.add_argument("--json", action="store_true", help="print JSON")
    args = parser.parse_args(argv)
    try:
        report = run(args.repo, args.readme or ["README.md"],
                     args.results or ["results"], args.include_code)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    print(json.dumps(report, indent=2) if args.json else format_text(report))
    return 0


if __name__ == "__main__":
    sys.exit(main())
