# GOAL Plan

## 1. Current Stable Baseline

All work must stay on server path `/home/ecs-user/tianchi_funds`.
Current stable branch and model anchor:

```text
branch             = codex/redeem-day30-conservative
doc commit         = 27ffb3f
stable model commit= b709daa
strategy           = redeem_low_variance_v3
artifact tag       = redeem_low_variance_v3_day21_128_day22_112_day26_112
```

Current stable metrics:

```text
overall weighted_relative_error_mean = 0.11831606502050732
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall bad_day_rate_max             = 0.11382113821138211
2014-08 Decision                     = PASS
```

## 2. Goal Definition

This goal upgrades the interface layer rather than only the rule layer or the compact method layer.
The purpose is to unlock new realistic candidates by allowing lightweight proxy-feature generation and a compact standalone modeling path that can still be evaluated through the existing server validation workflow.

Primary stretch target:

```text
overall weighted_relative_error_mean <= 0.11750000000000000
```

This is an interface-upgrade goal, not a guaranteed-target goal.
A retained candidate does not need to hit the stretch target immediately.
Any interface-upgrade candidate may be retained if it passes the keep rule below and shows real improvement.

Mandatory floor constraints for every retained version:

```text
2014-08 Decision                     == PASS
2014-08 weighted_relative_error_mean <= 0.11724453093435727
overall bad_day_rate_max             <= 0.11382113821138211
```

Goal completion rule:

- Success by stretch target: a retained version reaches `overall <= 0.11750000000000000` while keeping the mandatory floor constraints.
- Success by retained upgrade: improved interface-upgrade versions may be kept along the way even if the stretch target is not yet reached.
- Exhaustion exit: if every task in `GOAL_TASK.md` has been executed or explicitly exhausted and no further realistic interface-upgrade candidate remains, end the goal by task exhaustion.

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
- Prefer upgrades that improve future modeling headroom, not only tiny numeric wins.

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
2. Perform read-only attribution, proxy-feature feasibility review, or narrow offline screening.
3. Select one unique candidate only.
4. Edit server code for that one candidate.
5. Run tagged baseline validation, rolling validation, and evaluate report.
6. Compare with current stable keep rule.
7. KEEP: retain code, update the root operation log markdown, commit, push, and move the stable anchor.
8. ROLLBACK: restore previous stable code, keep tagged artifacts, update the root operation log markdown, and do not commit failed code.
```

## 6. Allowed Interface-Upgrade Space

The goal should prefer these directions in order:

1. Proxy-feature generation for future-known calendar or recent-history-derived signals that remain legal at prediction time
2. A compact standalone modeling path that trains on daily features and predicts purchase or redeem through a separate strategy path
3. A two-stage pipeline where stable rule predictions are used as base features for a lightweight second stage
4. A lightweight monthly or rolling calibration layer fed by proxy features rather than unavailable future fields
5. A minimal ensemble between the stable rule strategy and one new standalone interface-upgrade challenger

The goal should avoid these directions unless all listed tasks are exhausted:

- giant model sweeps
- heavy deep learning stacks
- broad hyperparameter search in one round
- simultaneous multi-family experiments in one round
- undocumented ad hoc interface changes without tagged validation
