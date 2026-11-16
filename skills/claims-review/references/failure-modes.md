# Failure modes of quantitative claims

Thirteen ways a headline number can be computed correctly and still not mean
what the README says. Each entry has a symptom, a detection recipe that
involves running something, and a fix recipe for the owner.

Use it as a list of experiments, not a list of accusations: most claims are
exposed to two or three of these, and a mode only becomes a finding when the
experiment moves the number.

| # | Mode | One-line test |
|---|------|---------------|
| 1 | Coincidental detection | Shift the alarms in time; how much recall survives? |
| 2 | One event carries the headline | Drop the largest event, site or year; recompute |
| 3 | Missing data counted as zero | Rerun with missing as missing |
| 4 | Tuned on the test period | Move every choice to the training period; rescore |
| 5 | Intervals from correlated samples | Resample blocks, not rows |
| 6 | Synthetic truth mirrors the estimator | Generate truth with a different mechanism |
| 7 | Hand-typed numbers drifted | Trace README numbers to results files |
| 8 | Ranking inside overlapping intervals | Interval on the paired difference |
| 9 | Detector and label share one rule | Score against independently defined events |
| 10 | Leakage through features or preprocessing | Rebuild features using past data only |
| 11 | Multiple comparisons | Count the variants tried; test the winner on fresh data |
| 12 | Survivorship and selection | Recompute on the full population |
| 13 | Unit, time-zone and alignment errors | Check magnitudes, DST days and join offsets |

---

## 1. Coincidental detection

**Symptom.** "Detects X% of events", where an event counts as detected if any
alarm falls anywhere inside its window. Long windows and frequent alarms make
a hit likely with no skill at all.

**Detect.** Compute the chance level and compare. Shift every alarm timestamp
by a set of offsets (circularly, by more than one event length, many offsets)
and recompute recall each time; the mean over shifts is chance recall.
Alternatively run the detector on data with no fault in it, or draw the same
number of alarms at random. Analytic check: with alarm rate r per hour and a
window of W hours, chance recall is about 1 - exp(-r * W).

**Fix.** Report recall, chance recall and excess recall (recall minus chance)
side by side. Shorten the matching window to what the use case needs, or count
a detection only within a lead time of the event start.

## 2. One event carries the headline

**Symptom.** A total, mean or percentage dominated by a single event, site,
customer or year; small n hidden behind a precise-looking number.

**Detect.** Rank the contributions to the headline. Drop the largest one and
recompute; then leave each unit out in turn and report the range. If the
conclusion flips or the number moves by more than its stated precision, the
headline is a statement about one event.

**Fix.** Report n, the leave-one-out range and the share of the largest
contributor. State the claim at the level the data supports ("in this one
year", "at this one site").

## 3. Missing data counted as zero

**Symptom.** `fillna(0)`, sums over series with gaps, default values on a
failed join, sensors that report 0 when offline. Totals come out low, averages
are biased, and gaps look like real events.

**Detect.** Count missing and exactly-zero values per series and per period.
Rerun the pipeline with missing kept as missing (skip those intervals, or
restrict to intervals where all inputs exist) and compare the headline. Check
whether "events" line up with data gaps.

**Fix.** Keep missing as missing, report coverage next to every aggregate, and
compare like with like (same intervals for both sides of a comparison).

## 4. Tuned on the test period

**Symptom.** A threshold, hyperparameter, feature set or model choice selected
using the same period that produces the reported score; a "hindcast" fitted
with data from after the target date; "held-out" data that was looked at
during development.

**Detect.** Find every choice in the pipeline and ask which rows informed it.
Move each choice to the training period (or to data strictly before the
target) and rescore the test period once. For time series, check that nothing
at time t uses data later than t.

**Fix.** Split into fit, selection and test periods in time order; freeze all
choices before touching the test period; report the test score once. If the
test period has already been used, say so and report the honest rerun.

## 5. Intervals from correlated samples

**Symptom.** A bootstrap or standard error that treats consecutive hours or
days, or rows from one site, as independent. Intervals come out several times
too narrow.

**Detect.** Measure the autocorrelation of the per-row errors or outcomes.
Recompute the interval resampling whole blocks (weeks, months, sites, events)
instead of rows, and compare widths. Rough check: effective n is about
n * (1 - rho) / (1 + rho) for lag-1 autocorrelation rho.

**Fix.** Block or cluster bootstrap with a block length longer than the
correlation; report the block length. For comparisons, bootstrap the paired
difference.

## 6. Synthetic truth mirrors the estimator

**Symptom.** A method validated on simulated data whose generator shares the
method's own assumptions: same functional form, same bookkeeping identity,
same noise model. Recovery is then guaranteed and proves little.

**Detect.** Read the generator next to the estimator and list the shared
assumptions. Regenerate the truth with a different mechanism (other functional
form, heavier-tailed noise, a violated assumption) and rerun the estimator.
Check whether an obviously wrong estimator would also "recover" the truth.

**Fix.** Validate against a truth produced independently of the method, or
against real labelled cases. State which assumptions the simulation shares
with the estimator.

## 7. Hand-typed numbers drifted

**Symptom.** README numbers that no results file contains; numbers that were
right two commits ago; tables pasted by hand.

**Detect.** Run `scripts/trace_numbers.py` on the repo. For every untraced or
near number, rerun the pipeline and compare. Also rerun the pipeline for the
traced headline numbers: a README can agree with a stale results file.

**Fix.** Generate README tables from the results files, or add a test that
fails when a README number is not in the results. Record corrections as
was / now / why.

## 8. Ranking inside overlapping intervals

**Symptom.** "A beats B", "best of five models", a league table, where the
differences are smaller than the uncertainty or no uncertainty is given.

**Detect.** Compute an interval on the paired difference between the top
candidates (same test cases, block bootstrap if correlated). Check whether the
ranking survives a different test period, seed or subset.

**Fix.** Report the difference with its interval. Where it includes zero, say
the candidates are not distinguishable on this data.

## 9. Detector and label share one rule

**Symptom.** Events are defined by a rule (value below a limit, flag set by a
heuristic) and the detector applies the same or a nearly equivalent rule to
the same signal. High agreement is then a tautology.

**Detect.** Compare the label definition and the detector logic line by line.
Measure how much of the score a trivial re-implementation of the label rule
achieves. Score against events defined from an independent source (a log, a
different signal, manual labels) if any exist.

**Fix.** Use independently defined events for scoring, or state plainly that
the number measures agreement between two versions of one rule.

## 10. Leakage through features or preprocessing

**Symptom.** Scaling, imputation, feature selection or target encoding fitted
on the full dataset before the split; features that include the target or a
future value (centred rolling windows, same-day actuals, post-event fields);
duplicated rows on both sides of a random split of a time series.

**Detect.** Trace each feature to the rows it was computed from. Refit
preprocessing on the training rows only, replace random splits of time series
with time-ordered splits, shift suspicious features by one step, and rescore.
A score that collapses was leaking.

**Fix.** Fit every transformation inside the training fold; split by time or
by group; build features with data available at prediction time only.

## 11. Multiple comparisons

**Symptom.** One striking result reported out of many variants, subgroups,
metrics, lags or time windows that were tried; "significant" with no count of
attempts.

**Detect.** Count the variants in the code, notebooks and history. Recompute
the reported effect for all of them and see where the headline sits in that
distribution. Test the selected variant on data not used for the selection, or
run a permutation test that repeats the whole selection.

**Fix.** Report the number of variants tried, correct for it, or confirm the
chosen variant on fresh data. Report the full table, not only the winner.

## 12. Survivorship and selection

**Symptom.** Results computed only on units that survived a filter correlated
with the outcome: sites with complete data, assets still operating, customers
who stayed, days when the system worked, "clean" periods.

**Detect.** Find every filter and count what it removed. Recompute the
headline on the unfiltered population (or with the excluded units at a
pessimistic value) and compare. Check whether exclusion happened before or
after the outcome was known.

**Fix.** Report the denominator before and after each filter, justify filters
that depend on the outcome, and give the headline on the full population as
well.

## 13. Unit, time-zone and alignment errors

**Symptom.** Totals off by a round factor (1000, 60, 4, 24); mixed power and
energy, or rates and totals; local time joined to UTC; 23- and 25-hour days;
interval-start joined to interval-end stamps; currency or price-base mixes.

**Detect.** Check magnitudes against a physical or business bound (capacity,
population, price range). Inspect the daylight-saving days and the row counts
per day. Shift one side of each join by one interval and see whether agreement
improves. Sum the same quantity by two routes and compare.

**Fix.** Convert to one unit and one time base at ingestion, name columns with
their unit, assert row counts per day, and keep a test with a DST day in it.
