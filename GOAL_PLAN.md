# GOAL Plan

## 1. Current Stable Baseline

All work must stay on server path `/home/ecs-user/tianchi_funds`.
Current stable branch and commit:

```text
branch        = codex/redeem-day30-conservative
stable commit = b709daa
strategy      = redeem_low_variance_v3
artifact tag  = redeem_low_variance_v3_day21_128_day22_112_day26_112
```

Current stable metrics:

```text
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall weighted_relative_error_mean = 0.11831606502050732
2014-06 weighted_relative_error_mean = 0.11407620724007135
2014-07 weighted_relative_error_mean = 0.11991147614877315
overall bad_day_rate_max             = 0.11382113821138211
2014-08 Decision                     = PASS
```

## 2. Goal Definition

This goal is no longer a last-digit micro-tuning goal.
It is a higher-level structure-upgrade goal.
The purpose is to spend multiple rounds testing conservative structural challengers and keep any retained structural version that produces real improvement under the server evaluation standard.

Primary stretch target:

```text
overall weighted_relative_error_mean <= 0.11810000000000000
```

However, this goal does not require hitting the stretch target in order to keep progress.
A structural candidate may be retained whenever it produces clear optimization effect under the keep rule defined below.

Mandatory floor constraints for every retained version:

```text
2014-08 Decision                     == PASS
2014-08 weighted_relative_error_mean <= 0.11724453093435727
overall bad_day_rate_max             <= 0.11382113821138211
```

Goal completion rule:

- Success by stretch target: a retained version reaches `overall <= 0.11810000000000000` while keeping the mandatory floor constraints.
- Success by retained structural improvement: the goal may keep improved structural versions along the way even if the stretch target is not reached yet.
- Exhaustion exit: if every task in `GOAL_TASK.md` has been executed or explicitly exhausted and no further realistic structural candidate remains, end the goal by task exhaustion.

## 3. Keep Rule For This Goal

This goal uses a more practical retention rule than the previous strict-all-metrics goal.
A candidate is allowed to KEEP when all of the following hold:

```text
1. 2014-08 Decision == PASS
2. 2014-08 weighted_relative_error_mean does not worsen
3. overall bad_day_rate_max does not worsen
4. overall weighted_relative_error_mean improves versus current stable anchor
```

Additional guidance:

- A small regression in `2014-06` or `2014-07` is allowed if the candidate still improves overall and respects the mandatory floor constraints above.
- Do not keep a candidate that materially damages one month just to gain a tiny overall improvement.
- Prefer candidates that improve both overall and structure robustness, not just the smallest numerical delta.

## 4. Hard Execution Constraints

- Only modify the server repo `/home/ecs-user/tianchi_funds`.
- Do not modify the local repo.
- All edits, tests, commits, pushes, and rollbacks must happen through server git.
- Goal-mode work must focus on execution, testing, evaluation, and decision-making only.
- Do not create new planning files during goal execution.
- Do not rewrite `GOAL_PLAN.md` or `GOAL_TASK.md` during goal execution.
- Append experiment outcomes only to the existing root operation log markdown file.
- Before every real code change, do read-only screening first.
- Each round may send only one candidate into real validation.
- Any failed candidate must be rolled back immediately in code, while tagged artifacts and logs are kept.
- Commit and push only when the keep rule passes.
- Restore generic untagged outputs before commit if they were refreshed.

## 5. Goal-Mode Operating Pattern

Each execution round must follow this order:

```text
1. Read current stable metrics and latest retained artifacts.
2. Perform read-only attribution, simulation, or narrow screening.
3. Select one unique candidate only.
4. Edit server code for that one candidate.
5. Run tagged baseline validation, rolling validation, and evaluate report.
6. Compare with current stable keep rule.
7. KEEP: retain code, update the root operation log markdown, commit, push, and move the stable anchor.
8. ROLLBACK: restore previous stable code, keep tagged artifacts, update the root operation log markdown, and do not commit failed code.
```

## 6. Allowed Optimization Space

The goal should prefer these structural directions in order:

1. Redeem hotspot overlap compression around the retained gated days
2. Redeem gate-shape refinement using existing signal style only
3. Purchase overlap precedence compression on one narrow region
4. Purchase month-end or local weekday overlap cleanup using existing rules only
5. One compact strategy challenger that changes structure but not model family

The goal should avoid these directions unless all listed tasks are exhausted:

- brand-new model families
- broad multi-parameter sweeps in one round
- simultaneous purchase and redeem multi-variable edits
- undocumented ad hoc changes without tagged validation
- reverting to trivial last-digit-only constant chasing as the main line
