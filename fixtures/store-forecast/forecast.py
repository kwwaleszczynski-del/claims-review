"""One-day-ahead sales forecast: weekday-profile model against a naive baseline.

Both forecasts for day t use only days before t. Scored on the last 90 days.

Usage:
    python forecast.py
"""
import csv
import json
import statistics
from pathlib import Path

HERE = Path(__file__).parent
TEST_DAYS = 90
PROFILE_WEEKS = 8


def load():
    with open(HERE / "data" / "sales.csv", newline="") as fh:
        return [float(r["units"]) for r in csv.DictReader(fh)]


def naive(units, t):
    """Same weekday last week."""
    return units[t - 7]


def profile(units, t):
    """Mean of the same weekday over the previous PROFILE_WEEKS weeks."""
    return statistics.fmean(units[t - 7 * k] for k in range(1, PROFILE_WEEKS + 1))


def mape(units, model, days):
    return 100 * statistics.fmean(abs(model(units, t) - units[t]) / units[t] for t in days)


def main():
    units = load()
    days = range(len(units) - TEST_DAYS, len(units))
    summary = {
        "test_days": TEST_DAYS,
        "mape_profile_pct": round(mape(units, profile, days), 2),
        "mape_naive_pct": round(mape(units, naive, days), 2),
    }
    (HERE / "results").mkdir(exist_ok=True)
    with open(HERE / "results" / "summary.json", "w") as fh:
        json.dump(summary, fh, indent=2)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
