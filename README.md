# claims-review

A Claude Code plugin that checks whether the numbers in a data-analysis
repository mean what its README says.

A headline number can be computed correctly and still mislead: recall that
random alarms would also reach, a score tuned on its own test year, a figure
typed into the README that the results file no longer contains. The author is
badly placed to see this, and a reviewer who is told the author's reasoning
tends to agree with it. This plugin hands the code, the data and the list of
claims, without the explanations, to an independent reviewer agent that reruns
and perturbs the analysis, then has each serious finding re-checked before it
is reported.

## What it does

1. **Trace** (deterministic, no model): `trace_numbers.py` lists every number
   in the README with its line and says whether a value in
   `results/**/*.json|csv` backs it within rounding.
2. **Extract** the headline claims from the README and docs.
3. **Review**: an independent `claims-reviewer` subagent gets the repository
   path, the claims and a checklist of failure modes. It works in a scratch
   copy and runs experiments: recompute the number, shift alarms in time, drop
   the largest event, treat missing data as missing, move tuned choices off
   the test period.
4. **Confirm**: a second, fresh agent tries to refute each HIGH finding.
5. **Report**: findings ranked HIGH / MEDIUM / LOW, each with `file:line`
   evidence, a minimal reproduction and the answer to "what would the number
   be by chance?".
6. Optionally, a "was / now / why" corrections entry for the owner.

The reviewed repository is never edited.

## Install

Requires Claude Code and Python 3.8+ (standard library only).

Run it from a local folder without installing:

```
git clone <this repository> claims-review
claude --plugin-dir ./claims-review
```

Then, inside Claude Code:

```
/claims-review:claims-review path/to/repo
/claims-review:claims-review path/to/repo --quick
```

The skill also triggers on requests such as "do the numbers in this repo hold
up?". The repository carries a single-plugin marketplace manifest, so once it
is hosted it can be installed with `/plugin marketplace add <owner>/<repo>`
and `/plugin install claims-review@claims-review`. See "What was verified" for
what has and has not been tested.

The helper also works on its own:

```
python skills/claims-review/scripts/trace_numbers.py path/to/repo
```

## Worked example

`fixtures/pump-anomaly` is a tiny synthetic repository whose README says:

> The detector catches **90%** of the logged faults (9 of 10) while raising
> only 49 alarm hours in a year of hourly data, about 0.94 per week.

The helper finds every headline number in the results file:

```
Results files: 2 (55 numeric values)
README numbers: 9 | 7 traced | 0 near | 1 UNTRACED | 1 minor | 0 skipped

file:line              number       status    source
README.md:8            90%          traced    results/summary.json:recall = 0.9
README.md:8            9            traced    results/summary.json:n_detected = 9
README.md:8            10           traced    results/summary.json:n_faults = 10
README.md:9            49           traced    results/summary.json:n_alarms = 49
README.md:9            0.94         traced    results/summary.json:alarms_per_week = 0.94
README.md:13           8760         traced    results/summary.json:n_hours = 8760
README.md:14           10           traced    results/summary.json:n_faults = 10
README.md:16           168          UNTRACED  -
README.md:16           4            minor     -
```

So the README agrees with the results. The review then reported (excerpt of
`eval/reports/pump-anomaly.md`, the output of the evaluation run):

```
### HIGH-1 The 90% recall is mostly coincidence: time-shifted alarms score 7.2 of 10  (confirmed)
- Claim: C1 "The detector catches **90%** of the logged faults (9 of 10)" (README.md:8)
- Failure mode: 1 Coincidental detection
- Evidence: detect.py:43 - a fault counts as detected if any alarm falls anywhere in
  its logged period; make_data.py:14 - the period is 240 h, so ten periods cover 27.4%
  of the year; make_data.py:34-36 - only 4 of the 10 faults leave any trace in the signal.
- Reproduction: in a scratch copy, import `detect`, shift the alarm hours circularly by
  every offset from 241 to 8519 h and recompute the share of faults with an alarm in
  their period; separately draw 49 random alarm hours; separately regenerate the data
  without the fault injection and rerun `detect.py`.
- Numbers: claimed 9/10; recomputed 9/10; by chance 7.2/10 under 8279 time-shifts
  (9 or more in 13.3% of shifts), 7.5/10 for random alarm hours, 0.75 analytically.
  On data with no fault injected the detector still scores 9/10.
- Suggested fix: report recall, chance recall and excess recall together (0.90, 0.72,
  0.18); count a detection only within a short lead time of the fault.
```

The same report has two MEDIUM and two LOW findings and a list of what the
claims survived.

## The checklist

`skills/claims-review/references/failure-modes.md` has a symptom, a detection
recipe and a fix recipe for each mode.

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

## Evaluation on the fixtures

`fixtures/` holds four tiny synthetic repositories: three with one planted
flaw each and one clean. `fixtures/ANSWERS.md` is the answer key and
`fixtures/verify_planted.py` recomputes the ground truth. Each reviewer got a
copy of one fixture folder placed outside this repository, so it could not
read the answer key. One run per fixture, full mode. Final reports are in
`eval/reports/`.

| Fixture | Planted flaw | Found as HIGH? | Reviewer's number (truth) | Re-check | Other findings |
|---------|--------------|----------------|---------------------------|----------|----------------|
| `pump-anomaly` | recall 0.9 is about 0.7 by chance | yes | chance 7.2 of 10 (7.3) | confirmed | 2 MEDIUM, 2 LOW |
| `store-forecast` | README MAPE 6.2% not in results | yes | 9.27% (9.27%) | confirmed | 1 MEDIUM, 1 LOW |
| `leak-alarm` | threshold tuned on the test year | yes | F1 0.38 (0.384) | confirmed | 1 MEDIUM, 1 LOW |
| `meter-calibration` | none | no HIGH (pass) | - | not needed | 2 MEDIUM, 1 LOW |

3 of 3 planted flaws found, 0 false HIGH findings on the clean fixture, 0
HIGH findings other than the planted ones. The chance figure differs slightly
from the answer key (7.2 against 7.3) because the reviewer used every hourly
offset and the key uses daily steps.

Read this result with its limits:

- **One run per fixture.** No repeats, so no estimate of how often a flaw
  would be missed.
- **The fixtures are easy.** Each is one short script with one flaw, runs in
  a second and ships its data generator, which the reviewers used to prove
  their points. Real repositories are larger and messier.
- **No baseline.** The same fixtures were not given to an agent without the
  checklist, so the evaluation does not show how much the plugin adds over a
  plain "review this repository" request.
- **The orchestrator was not blind.** The standalone `claude` command on the
  test machine was not logged in, so the flow could not be run unattended
  through the installed plugin. The author's session carried out the skill's
  steps by hand (helper, verbatim claim list, brief built only from the parts
  step 3 allows, confirmation, report) and launched the reviewer and re-check
  agents. Those agents were blind; the session writing their briefs was not.
- **The reviewer ran as a general-purpose agent** that was given the body of
  `agents/claims-reviewer.md` as instructions, so the read-only tool
  restriction was not enforced by the harness. A file comparison after the
  runs showed all four reviewed copies unchanged.
- **Reports were assembled in English** from the reviewers' output; two
  reviewers answered in another language because of a user-level setting in
  the test session. The agent definition now says to answer in the language
  of the brief; that change was made after the run.
- The MEDIUM findings on the clean fixture are real properties of it (the
  gain is concentrated in the high-flow half-year; the interval widens with
  longer blocks). Neither overturns its headline.
- Two re-check agents cited a line number off by one in their prose; the line
  numbers in the final reports were checked against the sources.

## Cost

Measured on the fixtures, as reported by the harness per subagent (total
tokens over the agent's whole run, including its fixed context):

| Agent | Runs | Tokens per run | Tool calls | Wall time |
|-------|------|----------------|------------|-----------|
| Reviewer | 4 | 82,700 to 87,400 | 5 to 6 | 2.2 to 3.2 min |
| Re-check of one HIGH finding | 3 | 73,300 to 75,000 | 3 | 0.7 to 0.9 min |

- **Quick mode** (`--quick`): the helper plus one reviewer, about 85,000
  subagent tokens per repository on these fixtures. HIGH findings are checked
  against the cited lines by the main session, with no second agent.
- **Full mode**: one reviewer, plus one re-check agent when there is any HIGH
  finding: about 160,000 subagent tokens with a HIGH finding, about 85,000
  without.

Not included: the main session's own tokens for extracting claims and writing
the report, which could not be measured separately here. Most of each figure
is fixed context of the test session (the re-check agents made three tool
calls and still used 73,000 tokens), so on a small repository the cost is
dominated by overhead; on a real repository expect the reviewer's share to
grow with the size of the code it has to read and the time its reruns take.
The helper alone costs nothing and runs in well under a second.

## Limits

- It finds reasons to doubt a number. It does not prove a number right. "No
  HIGH findings" means the claims survived the experiments listed in the
  report, nothing more.
- The reviewer can only run what runs: with missing data, credentials, heavy
  dependencies or long training jobs it falls back to reading, and such
  findings are capped at MEDIUM.
- The reviewer is a language model. It can misread code, design an unfair
  placebo or miscount a line. The confirmation step lowers that risk for HIGH
  findings only. The owner should rerun the reproduction before changing a
  headline.
- The helper matches numbers, not meanings. A README number can be "traced"
  to an unrelated value that happens to round the same way, and a correct
  derived number (a difference, a ratio) shows as UNTRACED. It reads
  `README.md` and `results/` by default and only JSON and CSV.
- Independence is procedural: the reviewer is not handed the author's
  explanations, but it can still read the README in the repository.

## What was verified

- `python -m unittest discover -s tests`: 19 tests of the helper pass.
- `claude plugin validate .` passes for the plugin and marketplace manifests
  (Claude Code 2.1.107).
- `claude --plugin-dir` loads the plugin: the session start event listed the
  skill `claims-review:claims-review` and the agent
  `claims-review:claims-reviewer`.
- Not verified: an unattended end-to-end run through the installed plugin
  (see above), installation from a hosted marketplace, and behaviour on
  macOS or Linux.

## Layout

```
.claude-plugin/plugin.json, marketplace.json
skills/claims-review/SKILL.md                    the flow
skills/claims-review/references/failure-modes.md the checklist
skills/claims-review/references/corrections-template.md
skills/claims-review/scripts/trace_numbers.py    deterministic helper
agents/claims-reviewer.md                        reviewer and re-check agent
tests/                                           helper unit tests
fixtures/                                        four synthetic repos, answer key
eval/reports/                                    reports from the evaluation run
```

## Licence

MIT, see `LICENSE`.
