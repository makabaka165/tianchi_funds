# GOAL Plan

## 1. Current Stable Baseline

All work must stay on server path `/home/ecs-user/tianchi_funds`.
Current stable branch and model anchor:

```text
branch              = codex/redeem-day30-conservative
doc commit          = 99165b2
stable model commit = b709daa
stable strategy     = redeem_low_variance_v3
stable artifact tag = redeem_low_variance_v3_day21_128_day22_112_day26_112
```

Current stable metrics:

```text
overall weighted_relative_error_mean = 0.11831606502050732
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall bad_day_rate_max             = 0.11382113821138211
2014-08 Decision                     = PASS
```

## 2. Goal Definition

This goal starts a new modeling system instead of extending the old rule-stack framework.
The purpose is to build and test one compact, independently modeled pipeline that can compete with the current stable anchor, while still using the same server-side validation and rollback discipline.

Primary stretch target:

```text
overall weighted_relative_error_mean <= 0.11720000000000000
```

This is a new-system goal, not a guaranteed-target goal.
A retained candidate does not need to hit the stretch target immediately.
Any new-system candidate may be retained if it passes the keep rule below and shows real improvement.

Mandatory floor constraints for every retained version:

```text
2014-08 Decision                     == PASS
2014-08 weighted_relative_error_mean <= 0.11724453093435727
overall bad_day_rate_max             <= 0.11382113821138211
```

Goal completion rule:

- Success by stretch target: a retained version reaches `overall <= 0.11720000000000000` while keeping the mandatory floor constraints.
- Success by retained upgrade: improved new-system versions may be kept along the way even if the stretch target is not yet reached.
- Exhaustion exit: if every task in `GOAL_TASK.md` has been executed or explicitly exhausted and no further realistic new-system candidate remains, end the goal by task exhaustion.

## 3. Keep Rule For This Goal

KEEP a candidate when all of the following hold against the current stable anchor:

```text
1. 2014-08 Decision == PASS
2. 2014-08 weighted_relative_error_mean does not worsen
3. overall bad_day_rate_max does not worsen
4. overall weighted_relative_error_mean improves versus current stable anchor
```

Additional guidance:

- `2014-06` and `2014-07` remain review metrics, not absolute blockers by default.
- Do not keep a candidate that clearly destabilizes one month just to gain a trivial overall delta.
- Prefer upgrades that create future modeling headroom, not only tiny numeric wins.

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

## 5. Allowed New-System Scope

This goal explicitly allows creating a small new modeling subsystem, including:

1. new Python modules under `src/` for feature assembly, training, inference, or calibration
2. one compact training/prediction entry path integrated with the existing artifact-tag workflow
3. separate purchase and redeem models if needed
4. lightweight proxy features and rolling-history features that are legal at prediction time
5. one compact blending layer between the new system and the stable anchor if justified

The goal should avoid these directions unless all listed tasks are exhausted:

- giant model sweeps
- heavy deep learning stacks
- broad hyperparameter search in one round
- simultaneous multi-family experiments in one round
- undocumented ad hoc interface changes without tagged validation

## 6. Goal-Mode Operating Pattern

Each execution round must follow this order:

```text
1. Read current stable metrics and latest retained artifacts.
2. Perform read-only feasibility review, feature audit, or narrow offline screening.
3. Select one unique candidate only.
4. Edit server code for that one candidate.
5. Run tagged baseline validation, rolling validation, and evaluate report.
6. Compare with current stable keep rule.
7. KEEP: retain code, update the root operation log markdown, commit, push, and move the stable anchor.
8. ROLLBACK: restore previous stable code, keep tagged artifacts, update the root operation log markdown, and do not commit failed code.
```
