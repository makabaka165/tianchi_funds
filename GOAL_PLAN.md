# GOAL Plan

## 1. Current Stable Baseline

All work must stay on server path `/home/ecs-user/tianchi_funds`.
Current stable branch and commit:

```text
branch        = codex/redeem-day30-conservative
stable commit = 5d9a471
strategy      = redeem_low_variance_v3
artifact tag  = redeem_low_variance_v3_day21_120
```

Current stable metrics:

```text
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall weighted_relative_error_mean = 0.12034015019631115
2014-06 weighted_relative_error_mean = 0.11832620007467828
2014-07 weighted_relative_error_mean = 0.12382962749024626
overall bad_day_rate_max             = 0.11382113821138211
2014-08 Decision                     = PASS
```

## 2. Goal Definition

This goal is intentionally medium-range:

- It must be harder than one or two trivial constant edits.
- It must still be realistic under the current conservative server-only workflow.
- It must require multiple rounds of analysis, screening, implementation, validation, and rollback decisions.

Primary target:

```text
overall weighted_relative_error_mean <= 0.11980000000000000
```

Required stability gates for every retained version:

```text
2014-08 weighted_relative_error_mean <= 0.11724453093435727
2014-06 weighted_relative_error_mean <= 0.11832620007467828
2014-07 weighted_relative_error_mean <= 0.12382962749024626
overall bad_day_rate_max             <= 0.11382113821138211
2014-08 Decision                     == PASS
```

Goal completion rule:

- If a retained server version reaches the primary target and all stability gates, the goal is achieved.
- If every task in `GOAL_TASK.md` has been executed or explicitly exhausted and the target is still not reached, then end the goal as completed-by-exhaustion rather than forcing unrealistic further work.

## 3. Hard Execution Constraints

- Only modify server repo `/home/ecs-user/tianchi_funds`.
- Do not modify local repo.
- All edits, tests, commits, pushes, and rollbacks must happen through server git.
- Goal-mode work must focus on execution, testing, evaluation, and decision-making.
- Do not create new planning files during goal execution.
- Do not replace this plan or task document during goal execution.
- You may append experiment outcomes to `????.md`.
- Before every real code change, do read-only screening first.
- Each round may send only one candidate into real validation.
- Any failed candidate must be rolled back immediately in code, while tagged artifacts and records must be kept.
- Commit and push only when all keep gates pass.
- Restore generic untagged outputs before commit if they were refreshed.

## 4. Goal-Mode Operating Pattern

Each execution round must follow this order:

```text
1. Read current stable metrics and latest artifacts.
2. Perform read-only attribution or simulation.
3. Select one unique candidate only.
4. Edit server code for that one candidate.
5. Run tagged baseline validation, rolling validation, and evaluate report.
6. Compare with current stable gates.
7. KEEP: retain code, update `????.md`, commit, push, move stable anchor.
8. ROLLBACK: restore previous stable code, keep artifacts, update `????.md`, no failed-code commit.
```

## 5. Allowed Optimization Space

The goal should prefer these directions in order:

1. Conservative redeem low-variance extension on top of `redeem_low_variance_v3`
2. Single-day gated redeem residual compression or uplift using only history-visible signals
3. Purchase-side structure attribution followed by one-at-a-time existing-rule edits
4. Small rule-order or overlap compression changes using existing logic only

The goal should avoid these directions unless all listed tasks are exhausted:

- brand-new model families
- large multi-parameter searches in one round
- purchase and redeem simultaneous multi-variable changes
- undocumented ad hoc code changes without tagged validation
