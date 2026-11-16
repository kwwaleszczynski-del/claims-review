# Fixture answer key

Four tiny synthetic repositories. Three carry one planted flaw each; one is
clean. Folder names and fixture READMEs give nothing away, and during the
evaluation each reviewer received a copy of a single fixture folder placed
outside this repository, so it could not read this file.

Ground-truth numbers below come from `python fixtures/verify_planted.py`.

| Fixture | Planted flaw | Checklist mode | README says | Truth |
|---------|--------------|----------------|-------------|-------|
| `pump-anomaly` | A fault counts as detected if any alarm falls in its ten-day logged period; random alarms at this rate mostly achieve that | 1 Coincidental detection | recall 90% (9 of 10) | chance recall 0.733 under 339 circular time-shifts of the alarms; excess 0.17 |
| `store-forecast` | README headline typed by hand and stale | 7 Hand-typed numbers drifted | MAPE 6.2% | `results/summary.json` and a rerun give 9.27% |
| `leak-alarm` | Alarm threshold chosen by maximising F1 on the test year (`evaluate.py`, `best_threshold(scores, labels)` on 2023 rows) | 4 Tuned on the test period | F1 0.60 on "held-out" 2023 | F1 0.384 with the threshold chosen on 2022 |
| `meter-calibration` | none | - | MAE 1.26 to 0.91, reduction 0.35 (0.17 to 0.52) | fit on 2022 only, scored once on 2023, paired weekly block bootstrap |

Scoring rule used in the evaluation:

- flawed fixture: **found** if the final report has a HIGH finding that names
  the planted mechanism and gives a recomputed number;
- clean fixture: **pass** if the final report has no HIGH finding.

Other HIGH findings on a flawed fixture are judged one by one against the
code and recorded as true or false positives.

Known side effects of how the fixtures were built, which a reviewer may
legitimately raise:

- `pump-anomaly`: only 4 of the 10 faults leave any trace in the signal
  (`make_data.py`), and the trace is a six-hour bump inside a ten-day period.
- `leak-alarm`: the 2023 pressure readings carry a constant offset
  (`make_data.py`, `DRIFT_2023`), which is why a threshold chosen on 2022
  transfers badly.
- all four: the data are synthetic and each generator is in the fixture.
