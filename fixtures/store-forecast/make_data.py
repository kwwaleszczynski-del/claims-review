"""Generate the synthetic daily sales series (deterministic).

Usage:
    python make_data.py
"""
import csv
import math
import random
from pathlib import Path

SEED = 7
DAYS = 730
WEEKDAY_FACTOR = [0.85, 0.90, 0.95, 1.00, 1.20, 1.35, 0.75]


def main():
    rng = random.Random(SEED)
    out = Path(__file__).parent / "data" / "sales.csv"
    with open(out, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["day", "weekday", "units"])
        for day in range(DAYS):
            level = 400 * (1 + 0.0003 * day) * (1 + 0.10 * math.sin(2 * math.pi * day / 365))
            units = level * WEEKDAY_FACTOR[day % 7] * math.exp(rng.gauss(0, 0.11))
            writer.writerow([day, day % 7, round(units)])


if __name__ == "__main__":
    main()
