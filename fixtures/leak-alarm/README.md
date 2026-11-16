# leak-alarm

A two-feature leak alarm for a pipe segment: daily pressure drop and flow gap
are combined into one score, and the alarm fires above a threshold.

## Result

The score is fitted on 2022. On the held-out year 2023 the alarm reaches an
F1 of **0.60** (precision 0.55, recall 0.66) over 365 days with 32 leak days.

## Method

- `data/segments.csv`: one row per day with `pressure_drop`, `flow_gap` and the
  confirmed `leak` label, for 2022 and 2023.
- `evaluate.py`: feature weights are the difference of class means on 2022;
  the alarm is then scored on 2023.

## Reproduce

    python make_data.py   # synthetic data, fixed seed
    python evaluate.py    # writes results/summary.json
