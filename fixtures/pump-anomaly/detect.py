"""Rolling z-score anomaly detector, scored against the maintenance fault log.

An hour raises an alarm when it deviates from the mean of the previous week by
more than K standard deviations. A logged fault counts as detected when one or
more alarms fall inside its logged period.

Usage:
    python detect.py
"""
import csv
import json
import math
from pathlib import Path

HERE = Path(__file__).parent
WINDOW_H = 168
K = 4.0


def load():
    with open(HERE / "data" / "vibration.csv", newline="") as fh:
        values = [float(r["vibration_mm_s"]) for r in csv.DictReader(fh)]
    with open(HERE / "data" / "faults.csv", newline="") as fh:
        faults = [(int(r["start_hour"]), int(r["end_hour"])) for r in csv.DictReader(fh)]
    return values, faults


def detect(values):
    alarms = []
    total = sum(values[:WINDOW_H])
    squares = sum(v * v for v in values[:WINDOW_H])
    for t in range(WINDOW_H, len(values)):
        mean = total / WINDOW_H
        std = math.sqrt(max(squares / WINDOW_H - mean * mean, 1e-12))
        if abs(values[t] - mean) > K * std:
            alarms.append(t)
        total += values[t] - values[t - WINDOW_H]
        squares += values[t] ** 2 - values[t - WINDOW_H] ** 2
    return alarms


def detected(alarms, faults):
    return [any(start <= t < end for t in alarms) for start, end in faults]


def main():
    values, faults = load()
    alarms = detect(values)
    hits = detected(alarms, faults)
    summary = {
        "n_hours": len(values),
        "n_faults": len(faults),
        "n_detected": sum(hits),
        "recall": round(sum(hits) / len(faults), 3),
        "n_alarms": len(alarms),
        "alarms_per_week": round(len(alarms) / (len(values) / 168), 2),
    }
    (HERE / "results").mkdir(exist_ok=True)
    with open(HERE / "results" / "summary.json", "w") as fh:
        json.dump(summary, fh, indent=2)
    with open(HERE / "results" / "alarms.csv", "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["alarm_hour"])
        writer.writerows([t] for t in alarms)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
