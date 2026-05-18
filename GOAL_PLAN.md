# GOAL Plan

## 1. Current Stable Baseline

All work must stay on server path `/home/ecs-user/tianchi_funds`.
Current stable branch and commit:

```text
branch        = codex/redeem-day30-conservative
stable commit = e343081
strategy      = redeem_low_variance_v3
artifact tag  = redeem_low_variance_v3_day21_128_day22_112
```

Current stable metrics:

```text
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall weighted_relative_error_mean = 0.11899309547780285
2014-06 weighted_relative_error_mean = 0.11562820632502605
2014-07 weighted_relative_error_mean = 0.12109582368744129
overall bad_day_rate_max             = 0.11382113821138211
2014-08 Decision                     = PASS
```

## 2. Goal Definition

This goal is intentionally harder than the previous one.
It should require multiple screening and validation rounds rather than one or two easy edits,
but it must still stay inside the current conservative server-only workflow.

Primary target:

```text
overall weighted_relative_error_mean <= 0.11830000000000000
```

Required hard stability gates for every retained version:

```text
2014-08 weighted_relative_error_mean <= 0.11724453093435727
2014-06 weighted_relative_error_mean <= 0.11562820632502605
2014-07 weighted_relative_error_mean <= 0.12109582368744129
overall bad_day_rate_max             <= 0.11382113821138211
2014-08 Decision                     == PASS
```

Goal completion rule:

- Success: a retained server version reaches the primary target and all hard stability gates.
- Exhaustion exit: if every task in `GOAL_TASK.md` has been executed or explicitly exhausted and the target is still not reached, then end the goal as completed by task exhaustion.
- The goal must not be kept open after the task list is exhausted.

## 3. Hard Execution Constraints

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
- Commit and push only when all hard keep gates pass.
- Restore generic untagged outputs before commit if they were refreshed.

## 4. Goal-Mode Operating Pattern

Each execution round must follow this order:

```text
1. Read current stable metrics and latest retained artifacts.
2. Perform read-only attribution, simulation, or narrow screening.
3. Select one unique candidate only.
4. Edit server code for that one candidate.
5. Run tagged baseline validation, rolling validation, and evaluate report.
6. Compare with current stable hard gates.
7. KEEP: retain code, update the root operation log markdown, commit, push, and move the stable anchor.
8. ROLLBACK: restore previous stable code, keep tagged artifacts, update the root operation log markdown, and do not commit failed code.
```

## 5. Allowed Optimization Space

The goal should prefer these directions in order:

1. Conservative retuning around the current `redeem_low_variance_v3` retained structure
2. One additional gated redeem single-day adjustment using only history-visible signals
3. One gated redeem structural compression or overlap control around the day21/day22 region
4. Purchase-side attribution followed by one-at-a-time existing-rule edits
5. One conservative overlap-order compression candidate using only existing logic

The goal should avoid these directions unless all listed tasks are exhausted:

- brand-new model families
- broad multi-parameter searches in one round
- simultaneous purchase and redeem multi-variable edits
- undocumented ad hoc code changes without tagged validation
- replacing the current evaluation standard with a looser one
