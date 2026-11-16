# Claims review: meter-calibration
Mode: full. Reviewed: 2 claims. HIGH 0, MEDIUM 2, LOW 1. No HIGH findings.
This review looks for reasons to doubt the numbers. A claim with no finding
survived the checks listed; it is not thereby proven.

## Claims
| ID | Claim | Where | Traced to results | Verdict |
|----|-------|-------|-------------------|---------|
| C1 | "A calibration fitted on 2022 and applied unchanged to 2023 lowers the mean absolute error of the daily reading from 1.26 to 0.91 m3/h" | README.md:7-8 | yes | holds under checks as an annual average; MEDIUM-1 |
| C2 | "a reduction of 0.35 m3/h (95% interval 0.17 to 0.52, paired block bootstrap over weeks)" | README.md:8-9 | yes | holds under checks; MEDIUM-2 |

## Findings
### MEDIUM-1 The whole reduction comes from the high-flow half of 2023
- Claim: C1 (README.md:7-8)
- Failure mode: 2 One event carries the headline (here one period)
- Evidence: make_data.py:23-25 - the raw bias is `3 - 0.08 * reference`, near zero at low flow; calibrate.py:46-47 reports only the annual mean.
- Reproduction: fit on 2022, compute the per-day gain on 2023, and bootstrap days 0-181 and 182-364 separately; leave out each week, 30-day and 91-day block.
- Numbers: claimed 0.35 over the year; 0.78 (0.53 to 1.01) in days 0-181 and -0.09 (-0.19 to 0.02) in days 182-364; by chance not applicable. Leave-one-out: 0.32 to 0.37 by week, 0.18 to 0.49 by quarter. The sign of the headline survives every drop.
- Suggested fix: report the reduction by flow level or half-year next to the annual figure.

### MEDIUM-2 The weekly block is shorter than the correlation in the paired difference
- Claim: C2 (README.md:8-9)
- Failure mode: 5 Intervals from correlated samples
- Evidence: calibrate.py:20 and :49-50 - `BLOCK_DAYS = 7`; the per-day gain also follows the seasonal flow level.
- Reproduction: same bootstrap with block lengths 1, 7, 14, 28 and 61 days.
- Numbers: claimed 0.17 to 0.52; recomputed 0.17 to 0.52 at 7 days, 0.14 to 0.58 at 14, 0.09 to 0.63 at 28, 0.01 to 0.71 at 61; by chance not applicable. Autocorrelation of the paired difference is 0.47 at lag 1 and 0.19 at lag 7. The interval excludes zero at every block length tried.
- Suggested fix: use monthly blocks or state that the interval is conditional on weekly blocks.

### LOW-1 Two README numbers are not in the results file
- Claim: "730 daily paired readings" (README.md:13), "95% interval" (README.md:9)
- Failure mode: 7 Hand-typed numbers drifted
- Numbers: both correct (730 rows; quantiles 2.5% and 97.5% at calibrate.py:68-69), only not machine-traceable.

## Raised but not confirmed
None.

## What the claims survived
- Recompute: `python calibrate.py` reproduces results/summary.json exactly; an independent least-squares fit gives 1.2598, 0.9133, 0.3465.
- Placebo: fitting with the meter-reference pairing shuffled (500 permutations) gives a mean "reduction" of -7.57; misaligning the 2023 pairs by 1, 7 and 30 days gives -0.12, -0.20, -0.17.
- Tuning and leakage: the fit uses 2022 only; fitting on 2023 itself gives 0.875 against 0.913 out of sample.
- Reverse direction (fit 2023, test 2022): 1.37 to 0.88.
- A constant offset alone gives 1.13, so the slope contributes.
- 200 fresh generator seeds: mean reduction 0.45 (0.31 to 0.58); a nonlinear meter with heavy-tailed noise: 0.41.
- Missing data: none.

## Not checked
- Mode 11 (no git history); modes 1, 8, 9, 12 not applicable; real data (the README says the data are synthetic).
