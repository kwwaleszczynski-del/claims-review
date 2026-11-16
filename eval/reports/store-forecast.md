# Claims review: store-forecast
Mode: full. Reviewed: 2 claims. HIGH 1, MEDIUM 1, LOW 1.
This review looks for reasons to doubt the numbers. A claim with no finding
survived the checks listed; it is not thereby proven.

## Claims
| ID | Claim | Where | Traced to results | Verdict |
|----|-------|-------|-------------------|---------|
| C1 | "On the last 90 days the weekday-profile model reaches a MAPE of **6.2%**" | README.md:7 | no | HIGH-1 |
| C2 | "against 12.58% for the naive same-weekday-last-week baseline" (profile beats naive) | README.md:8 | yes | holds under checks; MEDIUM-1 |

## Findings
### HIGH-1 The headline MAPE of 6.2% is not in the results; the code gives 9.27%  (confirmed)
- Claim: C1 "On the last 90 days the weekday-profile model reaches a MAPE of **6.2%**" (README.md:7)
- Failure mode: 7 Hand-typed numbers drifted
- Evidence: results/summary.json:3 - `"mape_profile_pct": 9.27`; forecast.py:42 - where the pipeline computes and writes it.
- Reproduction: `python forecast.py` in a scratch copy (the helper had already flagged 6.2% as UNTRACED).
- Numbers: claimed 6.2%; recomputed 9.27%; by chance not applicable (the README does not match its own results file). No other reading gives 6.2: profile lengths of 1 to 52 weeks give 8.75 to 12.58, other end windows 9.16 to 13.75, median APE 7.17, WAPE 9.59; none of the 585 rolling 90-day windows is below 7.88. A forecast using the generator's noise-free level scores 8.34, so 6.2 is below what the data allow.
- Suggested fix: correct the README to 9.27% and generate the sentence from results/summary.json, or add a test that fails when a README number is not in the results.

### MEDIUM-1 The data generator has exactly the structure the profile model assumes
- Claim: C1 + C2, profile beats naive (README.md:7-8)
- Failure mode: 6 Synthetic truth mirrors the estimator
- Evidence: make_data.py:13,23-24 - fixed weekday factors, smooth level, independent noise; forecast.py:30 - mean of the same weekday.
- Reproduction: regenerate with 500 other seeds and compare both models on the last 90 days.
- Numbers: profile wins in 500 of 500 seeds (mean 9.47 against 12.38); by chance not applicable - averaging eight independent draws beats one draw by construction. No alternative generator was run, hence MEDIUM.
- Suggested fix: test on real sales, or on a generator with holidays, promotions and correlated noise.

### LOW-1 The row count 730 is typed by hand
- Claim: "`data/sales.csv`: 730 days of unit sales." (README.md:12)
- Failure mode: 7 Hand-typed numbers drifted
- Numbers: claimed 730; recomputed 730. Correct, only not machine-traceable.

## Raised but not confirmed
None.

## What the claims survived
- C2: 12.58% reproduces exactly.
- Direction of C1 + C2 with the corrected number (9.27 against 12.58, difference 3.31 points): paired bootstrap interval 1.80 to 4.86 (daily blocks), 1.99 to 4.82 (weekly), 1.91 to 5.13 (two-weekly); positive in all 585 rolling 90-day windows; dropping the largest day gives 9.30 against 12.32; leave-one-week-out difference 2.99 to 3.81.
- Placebo: a profile with the wrong lag scores 18.1 to 20.7%, a flat 56-day mean 18.75%.
- Tuning: choosing the profile length on days 364-639 gives 8 weeks, as in the code; the best length on the test window would be 6.
- Leakage: forecast.py:25,30 uses only indices t - 7k.
- Missing data: none.

## Not checked
- Where 6.2% came from (no git history in the copy).
- Mode 6 with a different generator; mode 11 (one model, one profile length in the code); mode 13 (daily index, no timestamps).
