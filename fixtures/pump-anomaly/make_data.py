"""Generate the synthetic pump vibration series and the fault log (deterministic).

Usage:
    python make_data.py
"""
import csv
import math
import random
from pathlib import Path

SEED = 3
HOURS = 8760
N_FAULTS = 10
FAULT_WINDOW_H = 240  # the maintenance log records a fault as a ten-day period


def main():
    rng = random.Random(SEED)
    values, ar = [], 0.0
    for t in range(HOURS):
        ar = 0.6 * ar + rng.gauss(0, 0.08)
        v = 2.0 + 0.15 * math.sin(2 * math.pi * t / 24) + ar
        if rng.random() < 0.005:  # process transients (start-ups, valve changes)
            v += rng.choice([-1, 1]) * rng.uniform(0.6, 1.2)
        values.append(v)

    starts = []
    while len(starts) < N_FAULTS:
        s = rng.randrange(400, HOURS - 300)
        if all(abs(s - o) > 500 for o in starts):
            starts.append(s)
    starts.sort()
    for i, s in enumerate(starts):
        if i % 3 == 0:  # some faults raise vibration for a few hours
            for t in range(s + 100, s + 106):
                values[t] += 0.6

    data = Path(__file__).parent / "data"
    with open(data / "vibration.csv", "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["hour", "vibration_mm_s"])
        for t, v in enumerate(values):
            writer.writerow([t, f"{v:.4f}"])
    with open(data / "faults.csv", "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["fault_id", "start_hour", "end_hour"])
        for i, s in enumerate(starts, start=1):
            writer.writerow([i, s, s + FAULT_WINDOW_H])


if __name__ == "__main__":
    main()
