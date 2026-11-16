# Claims review: pump-anomaly
Mode: full. Reviewed: 2 claims. HIGH 1, MEDIUM 2, LOW 2.
This review looks for reasons to doubt the numbers. A claim with no finding
survived the checks listed; it is not thereby proven.

## Claims
| ID | Claim | Where | Traced to results | Verdict |
|----|-------|-------|-------------------|---------|
| C1 | "The detector catches **90%** of the logged faults (9 of 10)" | README.md:8 | yes | HIGH-1, MEDIUM-2 |
| C2 | "while raising only 49 alarm hours in a year of hourly data, about 0.94 per week" | README.md:8-9 | yes | arithmetic holds; MEDIUM-1, LOW-1 |

## Findings
### HIGH-1 The 90% recall is mostly coincidence: time-shifted alarms score 7.2 of 10  (confirmed)
- Claim: C1 "The detector catches **90%** of the logged faults (9 of 10)" (README.md:8)
- Failure mode: 1 Coincidental detection
- Evidence: detect.py:43 - a fault counts as detected if any alarm falls anywhere in its logged period; make_data.py:14 - the period is 240 h, so ten periods cover 27.4% of the year; make_data.py:34-36 - only 4 of the 10 faults leave any trace in the signal.
- Reproduction: in a scratch copy, import `detect`, shift the alarm hours circularly by every offset from 241 to 8519 h and recompute the share of faults with an alarm in their period; separately draw 49 random alarm hours; separately regenerate the data without the fault injection and rerun `detect.py`.
- Numbers: claimed 9/10; recomputed 9/10; by chance 7.2/10 under 8279 time-shifts (9 or more in 13.3% of shifts), 7.5/10 for random alarm hours, 0.75 analytically. On data with no fault injected the detector still scores 9/10. With a matching window of 48 h it scores 3/10 against 2.25 by chance. Only 2 faults have an alarm inside their injected signature.
- Suggested fix: report recall, chance recall and excess recall together (0.90, 0.72, 0.18); count a detection only within a short lead time of the fault, not anywhere in a ten-day period.

### MEDIUM-1 44 of 49 alarms are process transients, so "only 49 alarm hours" says nothing about false alarms
- Claim: C2 (README.md:8-9)
- Failure mode: other (no precision reported next to recall)
- Evidence: make_data.py:23-24 - random transients; detect.py:35 - the 4-sigma rule fires on them.
- Reproduction: replay the generator's random sequence to list transient hours and intersect with results/alarms.csv.
- Numbers: claimed 49 alarms, 0.94 per week; recomputed 49 and 0.94; by chance not applicable. 44 of 49 alarms sit on transients, 5 on injected fault hours; precision against the real fault signature is 5/49.
- Suggested fix: report precision, or alarms outside fault periods, next to recall.

### MEDIUM-2 Ten faults from one synthetic realisation; the interval on 9/10 includes the chance level
- Claim: C1 (README.md:8)
- Failure mode: 2 One event carries the headline / 6 Synthetic truth mirrors the estimator
- Evidence: make_data.py:11-13 - one seed, ten faults.
- Reproduction: exact binomial interval on 9/10; rerun the generator and detector for 200 other seeds.
- Numbers: claimed 90%; 95% interval 55.5% to 99.7%; by chance 72%. Other seeds average 7.5/10 with faults and 6.6/10 without; 9 or more in 23% of seeds.
- Suggested fix: state n, give the interval, and report the result over many seeds.

### LOW-1 Alarms per week divides by hours in which the detector cannot fire
- Claim: C2 "about 0.94 per week" (README.md:9)
- Failure mode: 13 Unit, time-zone and alignment errors (denominator)
- Evidence: detect.py:32 - the loop starts at hour 168; detect.py:56 - the rate divides by all 8760 h.
- Numbers: claimed 0.94; recomputed 0.96 over evaluated hours; by chance not applicable.

### LOW-2 Window 168 h and K = 4 have no selection period
- Claim: C1 (README.md:8)
- Failure mode: 4 Tuned on the test period
- Evidence: detect.py:16-17 - constants, scored on the whole year.
- Numbers: over a grid of windows and thresholds recall is 5 to 10 of 10 and excess over chance never exceeds 2.1; choosing on the first half-year and scoring the second does not move the result.

## Raised but not confirmed
None.

## What the claims survived
- C1 and C2 as arithmetic: `python make_data.py && python detect.py` regenerates data and results byte-identical to the repository.
- Missing data: none (8760 rows, no blanks or zeros).
- Leakage: the rolling window uses only the 168 hours before each hour (read, not run).

## Not checked
- Modes 5, 8, 11, 12: no intervals, rankings, variants or filters in the repository. No git history in the copy.
- Real data: the repository contains synthetic data only.
