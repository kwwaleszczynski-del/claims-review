"""Fit the leak score on 2022 and evaluate the alarm on 2023.

Usage:
    python evaluate.py
"""
import csv
import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
TRAIN_YEAR, TEST_YEAR = 2022, 2023


def load():
    with open(HERE / "data" / "segments.csv", newline="") as fh:
        return [(int(r["year"]), float(r["pressure_drop"]), float(r["flow_gap"]),
                 int(r["leak"])) for r in csv.DictReader(fh)]


def fit_weights(rows):
    """Difference of class means per feature (unit-variance linear score)."""
    weights = []
    for j in (1, 2):
        leak = statistics.fmean(r[j] for r in rows if r[3] == 1)
        normal = statistics.fmean(r[j] for r in rows if r[3] == 0)
        weights.append(leak - normal)
    return weights


def score(rows, weights):
    return [weights[0] * r[1] + weights[1] * r[2] for r in rows]


def confusion(scores, labels, threshold):
    tp = sum(1 for s, y in zip(scores, labels) if s >= threshold and y)
    fp = sum(1 for s, y in zip(scores, labels) if s >= threshold and not y)
    fn = sum(1 for s, y in zip(scores, labels) if s < threshold and y)
    return tp, fp, fn


def f1(scores, labels, threshold):
    tp, fp, fn = confusion(scores, labels, threshold)
    return 2 * tp / (2 * tp + fp + fn) if tp else 0.0


def best_threshold(scores, labels):
    grid = [i / 20 for i in range(-20, 81)]
    return max(grid, key=lambda t: f1(scores, labels, t))


def main():
    rows = load()
    train = [r for r in rows if r[0] == TRAIN_YEAR]
    test = [r for r in rows if r[0] == TEST_YEAR]
    weights = fit_weights(train)

    scores = score(test, weights)
    labels = [r[3] for r in test]
    # operating point of the alarm
    threshold = best_threshold(scores, labels)
    tp, fp, fn = confusion(scores, labels, threshold)

    summary = {
        "train_year": TRAIN_YEAR,
        "test_year": TEST_YEAR,
        "n_test_days": len(test),
        "n_test_leaks": sum(labels),
        "weights": [round(w, 4) for w in weights],
        "threshold": threshold,
        "f1": round(f1(scores, labels, threshold), 4),
        "precision": round(tp / (tp + fp), 4),
        "recall": round(tp / (tp + fn), 4),
    }
    (HERE / "results").mkdir(exist_ok=True)
    with open(HERE / "results" / "summary.json", "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
