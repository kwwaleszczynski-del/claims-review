# Corrections entry: was / now / why

For the repository owner, after a finding has been verified and fixed. One
entry per corrected claim, newest first, in `CORRECTIONS.md` or a README
section. Fill it only with numbers recomputed after the fix.

```
## <date> - <claim in a few words>

- Was: "<the sentence or number as it stood>" (<file>:<line> at <commit>)
- Now: "<the corrected sentence or number>"
- Why: <what was wrong, in one or two sentences, naming the failure mode>
- How found: <experiment that exposed it, with the command>
- Effect on conclusions: <unchanged | weakened | reversed>, <one sentence>
- Guard: <test or generated table that prevents a repeat, or "none yet">
```

Example:

```
## 2026-01-15 - fault detection rate

- Was: "The detector catches 90% of the logged faults (9 of 10)" (README.md:8 at 3f2a1c9)
- Now: "9 of 10 logged fault periods contain an alarm; 7.3 of 10 do when the
  alarms are shifted in time, so the excess over chance is 1.7 faults."
- Why: Coincidental detection. A fault counted as detected if any alarm fell
  in its ten-day period, which random alarms at this rate mostly achieve.
- How found: circular time-shift of the alarm list, 339 shifts, `python placebo.py`
- Effect on conclusions: weakened. The detector is not shown to be better than
  chance at this window length.
- Guard: results/summary.json now carries chance_recall and excess_recall;
  the README table is generated from it.
```

If a finding is rejected instead, record that too:

```
## <date> - <finding title> (rejected)

- Finding: <one sentence>
- Evidence against: <file>:<line>, <command and output that refute it>
```
