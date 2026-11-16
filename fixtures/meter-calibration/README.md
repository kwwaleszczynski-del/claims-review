# meter-calibration

Linear calibration of a low-cost flow meter against a reference meter.

## Result

A calibration fitted on 2022 and applied unchanged to 2023 lowers the mean
absolute error of the daily reading from 1.26 to 0.91 m3/h, a reduction of
0.35 m3/h (95% interval 0.17 to 0.52, paired block bootstrap over weeks).

## Method

- `data/readings.csv`: 730 daily paired readings, 365 per year.
- `calibrate.py`: least-squares fit of reference on meter using 2022 only;
  2023 is used once, for scoring. The interval resamples whole weeks of 2023
  (2000 draws, fixed seed) because the meter error is correlated between days.

## Limits

One meter, one site, two years. The result says nothing about other meters or
about drift beyond 2023. The data are synthetic.

## Reproduce

    python make_data.py   # synthetic data, fixed seed
    python calibrate.py   # writes results/summary.json
