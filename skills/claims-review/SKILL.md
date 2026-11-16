---
name: claims-review
description: Review whether the quantitative claims of a data-analysis repository hold - the headline numbers, rankings, "detects X%" and "within Y%" statements in its README and docs. Launches an independent reviewer subagent that reruns and perturbs the analysis (recompute, time-shifted placebo, drop the largest event, missing as missing), confirms each HIGH finding in source, and reports findings ranked HIGH/MEDIUM/LOW with file:line evidence and a reproduction. Use whenever the user asks to audit, sanity-check, fact-check, red-team or substantively review the results, numbers, metrics or README claims of an analysis, model evaluation, benchmark, backtest or notebook repo, or asks "do these numbers hold up?", "is this result real or chance?", "review my results before I publish" - even if they do not say "claims".
argument-hint: "[repo-path] [--quick]"
---

# Claims review

Check whether the numbers a data-analysis repository reports mean what its
README says. The review finds reasons to doubt a number; it cannot prove a
number right. Say so in the report.

**Target:** `$ARGUMENTS` - a repository path, optionally followed by `--quick`.
With no path, review the current working directory.

Three rules shape the whole flow:

- **Independence.** The reviewer gets code, data and the list of claims. It
  does not get the author's explanations of why the numbers are right, nor
  your own impressions. A reviewer handed a conclusion tends to return it
  confirmed.
- **Run, do not only read.** Reading finds suspicions; an experiment that
  moves the number makes a finding. Every HIGH finding carries a reproduction
  that was executed.
- **Hands off the reviewed repository.** All reruns happen in a scratch copy.
  Nothing in the reviewed repository is edited, including by you. Fixing is
  the owner's job after the report.

## Step 1 - Trace the README numbers (deterministic)

Run the bundled helper. It lists every number in the README with its line and
says whether a value in `results/**/*.json|csv` backs it within rounding.

```
python "${CLAUDE_SKILL_DIR}/scripts/trace_numbers.py" <repo>
```

Add `--readme <file>` for other markdown files that carry claims and
`--results <dir>` if results live elsewhere (both repeatable). `UNTRACED` and
`near` numbers go to the reviewer as leads. `traced` only means README and
results file agree, not that the number is right.

## Step 2 - Extract the headline claims

Read the README and any results docs. List the claims a reader would repeat:
levels ("MAPE 6.2%"), rates ("detects 90% of faults"), bounds ("within 5%"),
comparisons and rankings ("beats the baseline", "best of five"), intervals.
For each: the quoted text, `file:line`, the number, and what it is claimed to
mean. Skip set-up facts (row counts, dates) unless a claim depends on them.

Keep to the claims that matter, normally 3 to 10. Number them C1, C2, ...
Copy quotes verbatim; do not paraphrase or add your judgement.

## Step 3 - Launch the reviewer

Use the `claims-review:claims-reviewer` agent. One reviewer per repository is
the default. Split into one reviewer per claim group only when the claims come
from separate pipelines that share no code, and launch those in parallel.

Build the brief from these parts and nothing else:

1. Absolute path of the repository.
2. The numbered claim list from step 2 (quote, file:line).
3. The helper output from step 1.
4. Absolute path of the checklist: `${CLAUDE_SKILL_DIR}/references/failure-modes.md`.
5. The instruction: "Review these claims following your method. Work in a
   scratch copy, never modify the repository. Recompute each headline number,
   then run the checklist experiments the claim is exposed to - at least:
   recompute; a placebo or time-shift for any detection or skill claim; drop
   the largest event, site or period; missing data as missing; every tuned
   choice moved off the test period. For each finding answer: what would the
   number be by chance?"

Leave out: why the author believes the numbers, known-limitations prose,
earlier review results, and your own guesses about what is wrong.

## Step 4 - Confirm each HIGH finding

A HIGH finding tells the owner a headline is wrong, so it is checked a second
time before it is reported.

- **Full mode (default):** launch one fresh `claims-review:claims-reviewer`
  per repository in re-check mode. Give it the repository path and, for each
  HIGH finding, only the claim, the evidence location and the experiment - not
  the first reviewer's reasoning. Ask it to try to refute each one and answer
  CONFIRMED, DOWNGRADED or NOT CONFIRMED with its own numbers.
- **Quick mode (`--quick`):** no second agent. Open the cited lines yourself
  and check that they say what the finding claims; mark the finding
  "confirmed in source by orchestrator, experiment not re-run".

Report CONFIRMED findings as HIGH. Report DOWNGRADED ones at their new level.
Move NOT CONFIRMED ones to a "Raised but not confirmed" section with the
reason - do not drop them silently, the owner may know which side is right.

## Step 5 - Report

Give the report in the conversation. Write it to a file only if the user asks,
and then outside the reviewed repository unless they say otherwise.

```
# Claims review: <repo name>
Mode: full | quick. Reviewed: <n> claims. HIGH <n>, MEDIUM <n>, LOW <n>.
This review looks for reasons to doubt the numbers. A claim with no finding
survived the checks listed; it is not thereby proven.

## Claims
| ID | Claim | Where | Traced to results | Verdict |
|----|-------|-------|-------------------|---------|
| C1 | "<quote>" | README.md:<line> | yes / no / near | holds under checks / HIGH-1 / MEDIUM-2 |

## Findings
### HIGH-1 <title>  (confirmed | confirmed in source only)
- Claim: C<n> "<quote>" (README.md:<line>)
- Failure mode: <number and name from the checklist>
- Evidence: <file>:<line> - <what happens there>
- Reproduction: <minimal command or script, run in a scratch copy>
- Numbers: claimed <x>; recomputed <y>; by chance <z>
- Suggested fix: <the fix recipe from the checklist, made specific>

### MEDIUM-1 ...
### LOW-1 ...

## Raised but not confirmed
## What the claims survived
## Not checked
```

Every finding answers "what would the number be by chance?" in its Numbers
line; write "not applicable" only when no chance baseline exists for that kind
of claim (for example a README number that simply does not match its results
file). If there are no HIGH findings, say so in the first line and do not
promote weaker findings to fill the space.

## Step 6 - Corrections entry (optional)

If the owner accepts a finding and fixes it, offer the "was / now / why"
entry from `references/corrections-template.md`. The owner verifies each
point first: fix it, or reject it with evidence. Draft the entry only from
numbers the owner has recomputed.

## Modes and cost

- **Full:** helper + one reviewer + one confirmation agent when there is any
  HIGH finding. Add reviewers only for separate pipelines.
- **Quick (`--quick`):** helper + one reviewer, HIGH findings checked against
  source by you. Use it for a first pass or many repositories.

For several repositories, run one review per repository; do not put two
repositories in one reviewer's brief.
