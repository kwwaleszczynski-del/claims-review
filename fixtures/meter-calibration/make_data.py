"""Generate synthetic paired readings: low-cost flow meter and reference meter.

Usage:
    python make_data.py
"""
import csv
import math
import random
from pathlib import Path

SEED = 11
DAYS = 730  # days 0-364 are year 2022, days 365-729 are year 2023


def main():
    rng = random.Random(SEED)
    out = Path(__file__).parent / "data" / "readings.csv"
    err = 0.0
    with open(out, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["year", "day", "reference_m3h", "meter_m3h"])
        for day in range(DAYS):
            reference = 50 + 12 * math.sin(2 * math.pi * day / 365) + rng.gauss(0, 6)
            err = 0.5 * err + rng.gauss(0, 0.9)  # day-to-day correlated meter error
            meter = 3.0 + 0.92 * reference + err
            writer.writerow([2022 + day // 365, day % 365, f"{reference:.3f}", f"{meter:.3f}"])


if __name__ == "__main__":
    main()
