"""Recompute the ground truth behind each planted flaw (see ANSWERS.md).

Not part of any fixture: a reviewer under evaluation is given a copy of one
fixture folder only and never sees this file or ANSWERS.md.

Usage:
    python fixtures/verify_planted.py
"""
import importlib.util
import json
from pathlib import Path

HERE = Path(__file__).parent


def load_module(path):
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def pump_anomaly():
    m = load_module(HERE / "pump-anomaly" / "detect.py")
    values, faults = m.load()
    alarms = m.detect(values)
    span = len(values) - m.WINDOW_H
    width = faults[0][1] - faults[0][0]
    recalls = []
    for shift in range(width, span - width + 1, 24):  # circular shifts of the alarms
        shifted = [m.WINDOW_H + (t - m.WINDOW_H + shift) % span for t in alarms]
        hits = m.detected(shifted, faults)
        recalls.append(sum(hits) / len(faults))
    return {"recall": sum(m.detected(alarms, faults)) / len(faults),
            "chance_recall_shifted_alarms": round(sum(recalls) / len(recalls), 3),
            "n_shifts": len(recalls)}


def store_forecast():
    m = load_module(HERE / "store-forecast" / "forecast.py")
    units = m.load()
    days = range(len(units) - m.TEST_DAYS, len(units))
    return {"readme_mape_pct": 6.2,
            "recomputed_mape_profile_pct": round(m.mape(units, m.profile, days), 2)}


def leak_alarm():
    m = load_module(HERE / "leak-alarm" / "evaluate.py")
    rows = m.load()
    train = [r for r in rows if r[0] == m.TRAIN_YEAR]
    test = [r for r in rows if r[0] == m.TEST_YEAR]
    weights = m.fit_weights(train)
    s_train, y_train = m.score(train, weights), [r[3] for r in train]
    s_test, y_test = m.score(test, weights), [r[3] for r in test]
    t_test = m.best_threshold(s_test, y_test)
    t_train = m.best_threshold(s_train, y_train)
    return {"f1_threshold_tuned_on_2023": round(m.f1(s_test, y_test, t_test), 3),
            "f1_threshold_tuned_on_2022": round(m.f1(s_test, y_test, t_train), 3),
            "threshold_2023": t_test, "threshold_2022": t_train}


if __name__ == "__main__":
    print(json.dumps({"pump-anomaly": pump_anomaly(),
                      "store-forecast": store_forecast(),
                      "leak-alarm": leak_alarm()}, indent=2))
