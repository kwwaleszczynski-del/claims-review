"""Fit a linear calibration on 2022 and score it on 2023.

The calibration (reference = a + b * meter) is fitted by least squares on 2022
only. 2023 is used once, for scoring. The interval on the MAE reduction is a
paired block bootstrap over whole weeks of 2023, because the meter error is
correlated from day to day.

Usage:
    python calibrate.py
"""
import csv
import json
import random
import statistics
from pathlib import Path

HERE = Path(__file__).parent
BOOTSTRAP_SEED = 2024
N_BOOT = 2000
BLOCK_DAYS = 7


def load(year):
    with open(HERE / "data" / "readings.csv", newline="") as fh:
        return [(float(r["meter_m3h"]), float(r["reference_m3h"]))
                for r in csv.DictReader(fh) if int(r["year"]) == year]


def fit(pairs):
    mx = statistics.fmean(m for m, _ in pairs)
    my = statistics.fmean(r for _, r in pairs)
    b = (sum((m - mx) * (r - my) for m, r in pairs)
         / sum((m - mx) ** 2 for m, _ in pairs))
    return my - b * mx, b


def percentile(sorted_values, q):
    return sorted_values[min(len(sorted_values) - 1, int(q * len(sorted_values)))]


def main():
    a, b = fit(load(2022))
    test = load(2023)
    raw_err = [abs(m - r) for m, r in test]
    cal_err = [abs(a + b * m - r) for m, r in test]
    mae_raw = statistics.fmean(raw_err)
    mae_cal = statistics.fmean(cal_err)

    blocks = [range(s, min(s + BLOCK_DAYS, len(test)))
              for s in range(0, len(test), BLOCK_DAYS)]
    rng = random.Random(BOOTSTRAP_SEED)
    reductions = []
    for _ in range(N_BOOT):
        days = [d for _ in blocks for d in rng.choice(blocks)]
        reductions.append(statistics.fmean(raw_err[d] for d in days)
                          - statistics.fmean(cal_err[d] for d in days))
    reductions.sort()

    summary = {
        "fit_year": 2022,
        "test_year": 2023,
        "n_test_days": len(test),
        "intercept": round(a, 3),
        "slope": round(b, 4),
        "mae_raw_m3h": round(mae_raw, 2),
        "mae_calibrated_m3h": round(mae_cal, 2),
        "mae_reduction_m3h": round(mae_raw - mae_cal, 2),
        "mae_reduction_ci95_low": round(percentile(reductions, 0.025), 2),
        "mae_reduction_ci95_high": round(percentile(reductions, 0.975), 2),
        "bootstrap": {"n": N_BOOT, "block_days": BLOCK_DAYS, "seed": BOOTSTRAP_SEED},
    }
    (HERE / "results").mkdir(exist_ok=True)
    with open(HERE / "results" / "summary.json", "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
