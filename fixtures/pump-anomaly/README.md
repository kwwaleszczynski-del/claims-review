# pump-anomaly

A rolling z-score detector for pump vibration, scored against the maintenance
fault log.

## Result

The detector catches **90%** of the logged faults (9 of 10) while raising only
49 alarm hours in a year of hourly data, about 0.94 per week.

## Method

- `data/vibration.csv`: 8760 hourly vibration readings (mm/s).
- `data/faults.csv`: 10 faults from the maintenance log, each logged as a period.
- `detect.py`: an hour is an alarm when it deviates from the mean of the
  previous 168 hours by more than 4 standard deviations. A fault counts as
  detected when an alarm falls inside its logged period.

## Reproduce

    python make_data.py   # synthetic data, fixed seed
    python detect.py      # writes results/summary.json and results/alarms.csv
