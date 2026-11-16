# Claims review: leak-alarm
Mode: full. Reviewed: 2 claims. HIGH 1, MEDIUM 1, LOW 1.
This review looks for reasons to doubt the numbers. A claim with no finding
survived the checks listed; it is not thereby proven.

## Claims
| ID | Claim | Where | Traced to results | Verdict |
|----|-------|-------|-------------------|---------|
| C1 | "The score is fitted on 2022." | README.md:8 | yes | true for the weights only; HIGH-1 |
| C2 | "On the held-out year 2023 the alarm reaches an F1 of **0.60** (precision 0.55, recall 0.66) over 365 days with 32 leak days." | README.md:8-9 | yes | HIGH-1, MEDIUM-1 |

## Findings
### HIGH-1 The alarm threshold is tuned on the 2023 test labels; with the threshold chosen on 2022 the F1 is 0.38  (confirmed)
- Claim: C2 (README.md:8-9)
- Failure mode: 4 Tuned on the test period
- Evidence: evaluate.py:58-61 - `scores` and `labels` come from the 2023 rows and `threshold = best_threshold(scores, labels)`; evaluate.py:47-49 - `best_threshold` returns the F1-maximising grid value. Only the weights (evaluate.py:56) use 2022.
- Reproduction (scratch copy):
  ```python
  import evaluate as e
  rows = e.load()
  tr = [r for r in rows if r[0] == 2022]; te = [r for r in rows if r[0] == 2023]
  w = e.fit_weights(tr)
  s_tr, y_tr = e.score(tr, w), [r[3] for r in tr]
  s_te, y_te = e.score(te, w), [r[3] for r in te]
  t = e.best_threshold(s_tr, y_tr)                           # 1.95
  print(t, e.confusion(s_te, y_te, t), e.f1(s_te, y_te, t))  # (28, 86, 4), 0.3836
  ```
- Numbers: claimed F1 0.60 (threshold 3.5, precision 0.55, recall 0.66, 38 alarm days); recomputed 0.38 with the 2022 threshold 1.95 (precision 0.25, recall 0.875, 114 alarm days); by chance 0.16 alarming every day, 0.18 with shuffled 2023 labels and the same threshold selection, 0.09 with time-shifted alarms. Over 500 bootstrap resamples of 2022 the 2023 F1 has a 5-95% range of 0.34 to 0.54.
- Suggested fix: choose the threshold on 2022 (or on a selection period before 2023), freeze it, score 2023 once and report that number; say the earlier figure used the test year.

### MEDIUM-1 A sensor offset in 2023 drives most of the gap, and only the test-tuned threshold absorbs it
- Claim: C2 (README.md:8-9)
- Failure mode: 4 Tuned on the test period, with 13 (level shift between periods)
- Evidence: make_data.py:13 and :25 - 0.6 is added to `pressure_drop` on every 2023 day; the README does not mention it.
- Reproduction: recentre 2023 `pressure_drop` by the label-free difference of yearly medians and score with the 2022 threshold.
- Numbers: claimed 0.60; 0.38 with the 2022 threshold; 0.52 after label-free recentring; by chance 0.16 to 0.18.
- Suggested fix: document the offset and correct for it without labels before applying a frozen threshold.

### LOW-1 "Confirmed leak label" describes synthetic labels whose generator matches the estimator
- Claim: "the confirmed `leak` label" (README.md:13-14)
- Failure mode: 6 Synthetic truth mirrors the estimator
- Evidence: make_data.py:24-26. Wording only; no alternative generator was run.

## Raised but not confirmed
None.

## What the claims survived
- Arithmetic: `python make_data.py && python evaluate.py` reproduces data and results exactly; 365 days and 32 leak days in 2023.
- The test-tuned 0.60 is well above chance; leave-one-month-out range 0.585 to 0.625; no single period carries it.
- Missing data: none. Row-level autocorrelation is negligible (0.075 labels, -0.032 scores).

## Not checked
- Mode 6 with a different generator; modes 7 and 11 (no git history or notebooks); real data.
