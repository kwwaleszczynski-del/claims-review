# store-forecast

One-day-ahead forecast of daily unit sales for a single store.

## Result

On the last 90 days the weekday-profile model reaches a MAPE of **6.2%**,
against 12.58% for the naive same-weekday-last-week baseline.

## Method

- `data/sales.csv`: 730 days of unit sales.
- `forecast.py`: the profile model predicts a day as the mean of the same
  weekday over the previous 8 weeks; the baseline repeats the same weekday of
  the previous week. Both use only days before the forecast day.

## Reproduce

    python make_data.py   # synthetic data, fixed seed
    python forecast.py    # writes results/summary.json
