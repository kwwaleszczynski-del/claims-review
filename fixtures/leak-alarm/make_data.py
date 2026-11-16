"""Generate the synthetic daily leak dataset (deterministic).

Usage:
    python make_data.py
"""
import csv
import random
from pathlib import Path

SEED = 16
DAYS = 365
LEAK_RATE = 0.10
DRIFT_2023 = 0.6  # the pressure sensor reads higher after its 2023 re-installation


def main():
    rng = random.Random(SEED)
    out = Path(__file__).parent / "data" / "segments.csv"
    with open(out, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["year", "day", "pressure_drop", "flow_gap", "leak"])
        for year, drift in ((2022, 0.0), (2023, DRIFT_2023)):
            for day in range(DAYS):
                leak = 1 if rng.random() < LEAK_RATE else 0
                pressure_drop = rng.gauss(1.2 if leak else 0.0, 1.0) + drift
                flow_gap = rng.gauss(0.8 if leak else 0.0, 1.0)
                writer.writerow([year, day, f"{pressure_drop:.4f}", f"{flow_gap:.4f}", leak])


if __name__ == "__main__":
    main()
