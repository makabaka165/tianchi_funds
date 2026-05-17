# Server Execution Plan

## 1. Current Baseline

Current stable baseline has been upgraded from `probe_redeem_day26_088`
to `redeem_low_variance_v1_f094`.

```text
workspace        = /home/ecs-user/tianchi_funds
branch           = codex/redeem-day30-conservative
strategy         = redeem_low_variance_v1
artifact-tag     = redeem_low_variance_v1_f094
latest commit    = 77bb423 Add redeem low-variance day15 challenger
```

Current stable metrics:

```text
2014-08 weighted_relative_error_mean = 0.11724453093435727
overall weighted_relative_error_mean = 0.12362644553455275
2014-06 weighted_relative_error_mean = 0.12369324869886839
2014-07 weighted_relative_error_mean = 0.1316748812927628
overall bad_day_rate_max             = 0.13821138211382114
overall weighted_proxy_score_mean    = 6.347288400234884
2014-08 Decision                     = PASS
```

## 2. Fixed Constraints

- All work stays on server path `/home/ecs-user/tianchi_funds`.
- Do not rely on local repo state.
- Each round must do read-only screening first.
- Each round may send only one candidate into real validation.
- Failed candidates must roll back code immediately, but keep artifacts and logs.
- Commit and push only when all hard gates pass.

## 3. Hard Keep Gates

```text
2014-08 weighted_relative_error_mean <= 0.11724453093435727
overall weighted_relative_error_mean <= 0.12362644553455275
2014-06 weighted_relative_error_mean <= 0.12369324869886839
2014-07 weighted_relative_error_mean <= 0.1316748812927628
overall bad_day_rate_max             <= 0.13821138211382114
2014-08 Decision                     == PASS
```

## 4. Next High-Level Directions

### 4.1 Redeem low-variance v2

Continue the already successful low-variance challenger line, still conservatively:

- redeem side only
- no new model
- only history-visible rolling ratio signals
- read-only screening first
- at most one extra single day in a future challenger round

### 4.2 Purchase structural audit

Purchase still contributes many weighted bad days, but recent direct overlap compression
failed strict gates. If purchase is revisited, start with attribution instead of code changes:

- separate overlap inflation from under-correction
- split effects by day groups, month groups, and weekday groups
- only real-test a purchase change if read-only simulation clears all gates

### 4.3 Documentation chain

Documentation maintenance must stay server-side:

- avoid fragile non-server overwrite flows for the Chinese-named docs
- update log first, then sync README and PLAN when baseline changes
- stop experiments first if literal question-mark corruption appears again

## 5. Standard Round Flow

```text
1. Read current stable baseline and latest tagged artifacts
2. Run server-side read-only screening
3. Select exactly one candidate
4. Run baseline_weekday_mean.py and rolling_validate.py
5. Compare with hard gates
6. Keep plus commit plus push if improved
7. Roll back code but keep artifacts if not improved
```

## 6. Doc Status

README, PLAN, and the operations log were cleaned into an ASCII-safe server format
to stop the current encoding corruption chain. This is the safe maintenance baseline
until a verified UTF-8-only server-side editor flow is introduced.

